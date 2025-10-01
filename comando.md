sudo virsh -c qemu:///system list --all
sudo virsh -c qemu:///system start manjaro1
sudo virsh -c qemu:///system shutdown manjaro1
sudo virsh -c qemu:///system destroy manjaro1
sudo virsh -c qemu:///system reboot manjaro1
sudo virsh -c qemu:///system managedsave manjaro1
sudo virsh -c qemu:///system start manjaro1
sudo virsh -c qemu:///system managedsave-remove manjaro1
