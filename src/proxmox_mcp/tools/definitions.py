"""
Tool descriptions for Proxmox MCP tools.
"""

# Node tool descriptions
GET_NODES_DESC = """List all nodes in the Proxmox cluster with their status, CPU, memory, and role information.

Example:
{"node": "pve1", "status": "online", "cpu_usage": 0.15, "memory": {"used": "8GB", "total": "32GB"}}"""

GET_NODE_STATUS_DESC = """Get detailed status information for a specific Proxmox node.

Parameters:
node* - Name/ID of node to query (e.g. 'pve1')

Example:
{"cpu": {"usage": 0.15}, "memory": {"used": "8GB", "total": "32GB"}}"""

# VM tool descriptions
GET_VMS_DESC = """List all virtual machines across the cluster with their status and resource usage.

Example:
{"vmid": "100", "name": "ubuntu", "status": "running", "cpu": 2, "memory": 4096}"""

EXECUTE_VM_COMMAND_DESC = """Execute commands in a VM via QEMU guest agent.

Parameters:
node* - Host node name (e.g. 'pve1')
vmid* - VM ID number (e.g. '100')
command* - Shell command to run (e.g. 'uname -a')

Example:
{"success": true, "output": "Linux vm1 5.4.0", "exit_code": 0}"""

VM_SNAPSHOT_LIST_DESC = """List snapshots for a VM.

Parameters:
node* - Host node name (e.g. 'pve1')
vmid* - VM ID number (e.g. '100')

Example:
{"name": "pre-change/20260114-0430/nginx-upgrade", "created": "2026-01-14T04:30:00"}"""

VM_SNAPSHOT_CREATE_DESC = """Create a snapshot for a VM.

Parameters:
node* - Host node name (e.g. 'pve1')
vmid* - VM ID number (e.g. '100')
name* - Snapshot name
include_memory - Include VM memory state (default false)
description - Optional description

Example:
{"success": true, "snapshot": "pre-change/20260114-0430/nginx-upgrade"}"""

VM_SNAPSHOT_ROLLBACK_DESC = """Rollback a VM to a snapshot.

Parameters:
node* - Host node name (e.g. 'pve1')
vmid* - VM ID number (e.g. '100')
name* - Snapshot name

Example:
{"success": true, "snapshot": "pre-change/20260114-0430/nginx-upgrade"}"""

VM_SNAPSHOT_DELETE_DESC = """Delete a VM snapshot.

Parameters:
node* - Host node name (e.g. 'pve1')
vmid* - VM ID number (e.g. '100')
name* - Snapshot name

Example:
{"success": true, "snapshot": "pre-change/20260114-0430/nginx-upgrade"}"""

LXC_SNAPSHOT_LIST_DESC = """List snapshots for an LXC container.

Parameters:
node* - Host node name (e.g. 'pve1')
vmid* - Container ID number (e.g. '100')

Example:
{"name": "auto-hourly-20260114-0549", "created": "2026-01-14T05:49:00"}"""

LXC_SNAPSHOT_CREATE_DESC = """Create a snapshot for an LXC container.

Parameters:
node* - Host node name (e.g. 'pve1')
vmid* - Container ID number (e.g. '100')
name* - Snapshot name

Example:
{"success": true, "snapshot": "auto-hourly-20260114-0549"}"""

LXC_SNAPSHOT_ROLLBACK_DESC = """Rollback an LXC container to a snapshot.

Parameters:
node* - Host node name (e.g. 'pve1')
vmid* - Container ID number (e.g. '100')
name* - Snapshot name

Example:
{"success": true, "snapshot": "auto-hourly-20260114-0549"}"""

LXC_SNAPSHOT_DELETE_DESC = """Delete an LXC snapshot.

Parameters:
node* - Host node name (e.g. 'pve1')
vmid* - Container ID number (e.g. '100')
name* - Snapshot name

Example:
{"success": true, "snapshot": "auto-hourly-20260114-0549"}"""

# Container tool descriptions
GET_CONTAINERS_DESC = """List all LXC containers across the cluster with their status and configuration.

Example:
{"vmid": "200", "name": "nginx", "status": "running", "template": "ubuntu-20.04"}"""

# Storage tool descriptions
GET_STORAGE_DESC = """List storage pools across the cluster with their usage and configuration.

Example:
{"storage": "local-lvm", "type": "lvm", "used": "500GB", "total": "1TB"}"""

# Cluster tool descriptions
GET_CLUSTER_STATUS_DESC = """Get overall Proxmox cluster health and configuration status.

Example:
{"name": "proxmox", "quorum": "ok", "nodes": 3, "ha_status": "active"}"""
