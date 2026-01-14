"""
VM-related tools for Proxmox MCP.

This module provides tools for managing and interacting with Proxmox VMs:
- Listing all VMs across the cluster with their status
- Retrieving detailed VM information including:
  * Resource allocation (CPU, memory)
  * Runtime status
  * Node placement
- Executing commands within VMs via QEMU guest agent
- Handling VM console operations

The tools implement fallback mechanisms for scenarios where
detailed VM information might be temporarily unavailable.
"""
from typing import List, Optional
from datetime import datetime
from mcp.types import TextContent as Content
from .base import ProxmoxTool
from .definitions import GET_VMS_DESC, EXECUTE_VM_COMMAND_DESC
from .console.manager import VMConsoleManager

class VMTools(ProxmoxTool):
    """Tools for managing Proxmox VMs.
    
    Provides functionality for:
    - Retrieving cluster-wide VM information
    - Getting detailed VM status and configuration
    - Executing commands within VMs
    - Managing VM console operations
    
    Implements fallback mechanisms for scenarios where detailed
    VM information might be temporarily unavailable. Integrates
    with QEMU guest agent for VM command execution.
    """

    def __init__(self, proxmox_api):
        """Initialize VM tools.

        Args:
            proxmox_api: Initialized ProxmoxAPI instance
        """
        super().__init__(proxmox_api)
        self.console_manager = VMConsoleManager(proxmox_api)

    def get_vms(self) -> List[Content]:
        """List all virtual machines across the cluster with detailed status.

        Retrieves comprehensive information for each VM including:
        - Basic identification (ID, name)
        - Runtime status (running, stopped)
        - Resource allocation and usage:
          * CPU cores
          * Memory allocation and usage
        - Node placement
        
        Implements a fallback mechanism that returns basic information
        if detailed configuration retrieval fails for any VM.

        Returns:
            List of Content objects containing formatted VM information:
            {
                "vmid": "100",
                "name": "vm-name",
                "status": "running/stopped",
                "node": "node-name",
                "cpus": core_count,
                "memory": {
                    "used": bytes,
                    "total": bytes
                }
            }

        Raises:
            RuntimeError: If the cluster-wide VM query fails
        """
        try:
            result = []
            for node in self.proxmox.nodes.get():
                node_name = node["node"]
                vms = self.proxmox.nodes(node_name).qemu.get()
                for vm in vms:
                    vmid = vm["vmid"]
                    # Get VM config for CPU cores
                    try:
                        config = self.proxmox.nodes(node_name).qemu(vmid).config.get()
                        result.append({
                            "vmid": vmid,
                            "name": vm["name"],
                            "status": vm["status"],
                            "node": node_name,
                            "cpus": config.get("cores", "N/A"),
                            "memory": {
                                "used": vm.get("mem", 0),
                                "total": vm.get("maxmem", 0)
                            }
                        })
                    except Exception:
                        # Fallback if can't get config
                        result.append({
                            "vmid": vmid,
                            "name": vm["name"],
                            "status": vm["status"],
                            "node": node_name,
                            "cpus": "N/A",
                            "memory": {
                                "used": vm.get("mem", 0),
                                "total": vm.get("maxmem", 0)
                            }
                        })
            return self._format_response(result, "vms")
        except Exception as e:
            self._handle_error("get VMs", e)

    def list_snapshots(self, node: str, vmid: str) -> List[Content]:
        """List snapshots for a VM."""
        try:
            snapshots = self.proxmox.nodes(node).qemu(vmid).snapshot.get()
            lines = [f"Snapshots for VM {vmid} on {node}:"]
            for snap in snapshots:
                name = snap.get("name", "unknown")
                snaptime = snap.get("snaptime")
                created = datetime.fromtimestamp(snaptime).isoformat() if snaptime else "unknown"
                lines.append(f"- {name} (created: {created})")
            return [Content(type="text", text="\n".join(lines))]
        except Exception as e:
            self._handle_error(f"list snapshots for VM {vmid}", e)

    def create_snapshot(
        self,
        node: str,
        vmid: str,
        name: str,
        include_memory: bool = False,
        description: Optional[str] = None,
    ) -> List[Content]:
        """Create a VM snapshot."""
        try:
            payload = {"snapname": name}
            if description:
                payload["description"] = description
            if include_memory:
                payload["vmstate"] = 1
            self.proxmox.nodes(node).qemu(vmid).snapshot.post(**payload)
            return [Content(type="text", text=f"Snapshot created: {name} for VM {vmid} on {node}")]
        except Exception as e:
            self._handle_error(f"create snapshot {name} for VM {vmid}", e)

    def rollback_snapshot(self, node: str, vmid: str, name: str) -> List[Content]:
        """Rollback a VM snapshot."""
        try:
            self.proxmox.nodes(node).qemu(vmid).snapshot(name).rollback.post()
            return [Content(type="text", text=f"Snapshot rollback started: {name} for VM {vmid} on {node}")]
        except Exception as e:
            self._handle_error(f"rollback snapshot {name} for VM {vmid}", e)

    def delete_snapshot(self, node: str, vmid: str, name: str) -> List[Content]:
        """Delete a VM snapshot."""
        try:
            self.proxmox.nodes(node).qemu(vmid).snapshot(name).delete()
            return [Content(type="text", text=f"Snapshot deleted: {name} for VM {vmid} on {node}")]
        except Exception as e:
            self._handle_error(f"delete snapshot {name} for VM {vmid}", e)

    async def execute_command(self, node: str, vmid: str, command: str) -> List[Content]:
        """Execute a command in a VM via QEMU guest agent.

        Uses the QEMU guest agent to execute commands within a running VM.
        Requires:
        - VM must be running
        - QEMU guest agent must be installed and running in the VM
        - Command execution permissions must be enabled

        Args:
            node: Host node name (e.g., 'pve1', 'proxmox-node2')
            vmid: VM ID number (e.g., '100', '101')
            command: Shell command to run (e.g., 'uname -a', 'systemctl status nginx')

        Returns:
            List of Content objects containing formatted command output:
            {
                "success": true/false,
                "output": "command output",
                "error": "error message if any"
            }

        Raises:
            ValueError: If VM is not found, not running, or guest agent is not available
            RuntimeError: If command execution fails due to permissions or other issues
        """
        try:
            result = await self.console_manager.execute_command(node, vmid, command)
            # Use the command output formatter from ProxmoxFormatters
            from ..formatting import ProxmoxFormatters
            formatted = ProxmoxFormatters.format_command_output(
                success=result["success"],
                command=command,
                output=result["output"],
                error=result.get("error")
            )
            return [Content(type="text", text=formatted)]
        except Exception as e:
            self._handle_error(f"execute command on VM {vmid}", e)
