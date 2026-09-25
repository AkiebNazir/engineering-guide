```arch
node router "Load Balancer / Router" at 1,0

group blue "Blue Environment (Active)"
node appv1_1 "App v1" in blue at 0,1
node appv1_2 "App v1" in blue at 0,2

group green "Green Environment (Idle/Testing)"
node appv2_1 "App v2" in green at 2,1
node appv2_2 "App v2" in green at 2,2

router -> appv1_1
router -> appv1_2
router -> appv2_1
router -> appv2_2
```
