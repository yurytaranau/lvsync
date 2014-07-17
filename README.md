lvsync
======
Logical Volume Sync Tool

Example
=====

**Task:**<br>
  We need to migrate logical volume (e.g. used by virtual machine) from host1 to host2 with minimal downtime.<br>
  Logical volume path (host1): <code>/dev/vg/disk1</code> (e.g. size: 10G)

**Solution:**<br>

 - Create on running virtual machine lvm-snapshot:<br>
    <code>lvcreate -s disk1-snap -L 1G vg/disk1</code>
 
 - Create new logical volume on remote host2 with same or bigger size:<br>
    <code>lvcreate -s disk1-mgr -L 10G vg</code>

 - Send new snapshot to remote host2 using dd or run:<br>
    <code>lvsync /dev/vg/disk1-snap root@host2:/dev/vg/disk1-mgr</code>


    First need to send created snapshot to remote server.
    Type 'no' if you has already sent volume manually).
    Command: dd if=/dev/vg/disk1-snap bs=1M | pv -ptrb | ssh root@host2 dd of=/dev/vg/disk1-mgr bs=1M
    Run sync? [yes/no]: yes


 - After you must shut down virtual machine and run script again to sync only chunks with changed data:
<code>lvsync /dev/vg/disk1-snap root@host2:/dev/vg/disk1-mgr</code>


    First need to send created snapshot to remote server.
    Type 'no' if you has already sent volume manually).
    Command: dd if=/dev/vg/disk1-snap bs=1M | pv -ptrb | ssh root@host2 dd of=/dev/vg/disk1-mgr bs=1M
    Run sync? [yes/no]: no
    
    Found 2672 changed chunks.
    Send chunks to remote volume? [yes/no]: yes

Links
======
Based on https://github.com/mpalmer/lvmsync
