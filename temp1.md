```arch
group VMs "Virtual Machines"
group Containers "Containers"

node VM_Host "Host OS" in VMs at 0,1
node VM_Hyper "Hypervisor" in VMs at 1,1
node VM1 "VM 1\n(Guest OS + App)" in VMs at 2,0
node VM2 "VM 2\n(Guest OS + App)" in VMs at 2,2

VM_Host -> VM_Hyper
VM_Hyper -> VM1
VM_Hyper -> VM2

node C_Host "Host OS" in Containers at 0,5
node C_Docker "Docker Engine" in Containers at 1,5
node C1 "Container 1\n(App + Libs)" in Containers at 2,4
node C2 "Container 2\n(App + Libs)" in Containers at 2,6

C_Host -> C_Docker
C_Docker -> C1
C_Docker -> C2
```
