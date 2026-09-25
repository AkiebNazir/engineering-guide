```arch
%% caption: A kill switch is one transactional write followed by a fan-out through relays, and every hop is a cache that keeps serving the last good version if the hop before it dies.
node Op "Operator" at 0,0 icon=user
node CP "Control Plane" at 2,0 icon=server
node Rel "Regional Relay" at 2,2 icon=internet
node SDK "SDK in Service" at 0,2 icon=code

Op -> CP : "POST flag:kill\nwith reason"
CP -> CP : "commit flag\n& audit" dir=right
CP -> Op : "200 OK\nversion N+1"
CP -> Rel : "publish\npatch N+1"
Rel -> SDK : "SSE patch\nversion N+1"
SDK -> SDK : "apply if\nN+1 > held" dir=left
SDK -> Rel : "poll if\nstream broken"
Rel -> SDK : "200 new\nsnapshot"
```
