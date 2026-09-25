```arch
group src "Source Control"
group ci "CI Server"
group runners "Runner Pool"
group outputs "Outputs"

node GH "GitHub / GitLab / Bitbucket" in src at 10, 0
node CTRL "Controller / Coordinator\n(Receives webhooks,\nschedules jobs)" in ci at 10, 10
node R1 "Runner 1\n(Ubuntu)" in runners at 0, 20
node R2 "Runner 2\n(macOS)" in runners at 10, 20
node R3 "Runner 3\n(Windows)" in runners at 20, 20
node R4 "Runner 4\n(Docker)" in runners at 30, 20

node ART "Artifacts\n(binaries, images)" in outputs at 0, 30
node REP "Reports\n(test results, coverage)" in outputs at 10, 30
node NOT "Notifications\n(Slack, email)" in outputs at 20, 30

GH -> CTRL
CTRL -> R1
CTRL -> R2
CTRL -> R3
CTRL -> R4
R1 -> ART
R1 -> REP
CTRL -> NOT
```
