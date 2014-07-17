lvsync
======

Logical Volume Sync Tool


Usage example
======
Task:<br>
  We need to migrate logical volume (e.g. used by virtual machine) from host1 to host2 with minimal downtime.<br>
  Logical volume path (host1): <code>/dev/vg/disk1</code> (e.g. size: 10G)

Solution:<br>
- Create on running virtual machine lvm-snapshot:<br>
lvcreate -s disk1-snap -L 1G vg/disk1

- Create new logical volume on remote host2 with same or bigger size:<br>
lvcreate -s disk1-mgr -L 10G vg

- Send new snapshot to remote host2 using dd or run:<br>
lvsync /dev/vg/disk1-snap root@host2:/dev/vg/disk1-mgr

      First need to send created snapshot to remote server.
      Type 'no' if you has already sent volume manually).
      Command: dd if=/dev/vg/disk1-snap bs=1M | pv -ptrb | ssh root@host2 dd of=/dev/vg/disk1-mgr bs=1M
      Run sync? [yes/no]: yes

Virtual machine can be runned<br>

- After you must shut down virtual machine and run script again to sync only chunks with changed data:
lvsync /dev/vg/disk1-snap root@host2:/dev/vg/disk1-mgr
  
      First need to send created snapshot to remote server.
      Type 'no' if you has already sent volume manually).
      Command: dd if=/dev/vg/disk1-snap bs=1M | pv -ptrb | ssh root@host2 dd of=/dev/vg/disk1-mgr bs=1M
      Run sync? [yes/no]: no

      Found 2672 changed chunks.
      Send chunks to remote volume? [yes/no]: yes
</code>

Links
======
Based on https://github.com/mpalmer/lvmsync
