```arch
node User "Docker Client" at 0,0
node Daemon "Docker Daemon" at 2,0
node Registry "Docker Registry\n(e.g., Docker Hub)" at 4,0

node step1 "docker build" at 1,1
node step2 "Builds image layers" at 3,2
node step3 "docker run" at 1,3
node step4 "Starts container" at 3,4
node step5 "docker push" at 1,5
node step6 "Uploads image layers" at 3,6
node step7 "docker pull" at 1,7
node step8 "Downloads image layers" at 3,8

User -> step1
step1 -> Daemon

Daemon -> step2
step2 -> Daemon

User -> step3
step3 -> Daemon

Daemon -> step4
step4 -> Daemon

User -> step5
step5 -> Daemon

Daemon -> step6
step6 -> Registry

User -> step7
step7 -> Daemon

Registry -> step8
step8 -> Daemon
```
