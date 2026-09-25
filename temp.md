```arch
%% caption: The gateway forwards the verified claim extracted from the token — never a raw header the caller could set themselves.
node client "Client" at 0,1
node gw "Edge / gateway\nvalidate token\nset deadline" at 1,1
node policy "Route policy (cached)\nresolve route + version" at 2,0
node quota "Quota buckets\ncheck safety buckets" at 2,2
node backend "Upstream backend service\nre-authorize\ntenant-scoped data access" at 3,1

client -> gw
gw -> policy
gw -> quota
gw -> backend
backend -> gw
gw -> client
```
