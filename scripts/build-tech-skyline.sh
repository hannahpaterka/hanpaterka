#!/usr/bin/env bash
# Builds assets/tech-skyline.svg — GitCity skyline with tech billboard signs on buildings.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSETS="$ROOT/assets"
mkdir -p "$ASSETS"

curl -sL "https://gitcity.natrajx.in/api/svg?u=hannahpaterka&theme=aurora" -o /tmp/gitcity.svg

encode_icon() {
  curl -sL -A "Mozilla/5.0" "$1" | base64 | tr -d '\n'
}

# url|gx|gy|style  — gx/gy in GitCity local coordinates (400x296)
# style: rooftop | facade | shop
declare -a SIGNS=(
  "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/react/react-original.svg|248|214|shop"
  "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/typescript/typescript-original.svg|188|156|facade"
  "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/java/java-original.svg|200|132|rooftop"
  "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/spring/spring-original.svg|158|186|shop"
  "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/nestjs/nestjs-plain.svg|212|148|facade"
  "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postgresql/postgresql-original.svg|224|168|facade"
  "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/redis/redis-original.svg|236|198|shop"
  "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg|206|118|rooftop"
  "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/graphql/graphql-plain.svg|272|176|facade"
  "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/apachekafka/apachekafka-original.svg|176|204|shop"
)

sign_svg() {
  local url="$1" gx="$2" gy="$3" style="$4"
  local b64 pole signw signh icon
  b64=$(encode_icon "$url")

  case "$style" in
    rooftop)  pole=6;  signw=24; signh=24; icon=16 ;;
    facade)   pole=10; signw=26; signh=26; icon=17 ;;
    shop)     pole=14; signw=28; signh=28; icon=18 ;;
    *)        pole=10; signw=26; signh=26; icon=17 ;;
  esac

  local bx=$(( -signw / 2 ))
  local by=$(( -signh - pole ))
  local ix=$(( bx + (signw - icon) / 2 ))
  local iy=$(( by + (signh - icon) / 2 ))

  cat <<EOF
  <g transform="translate(${gx},${gy})">
    <line x1="0" y1="0" x2="0" y2="${pole}" stroke="#c4b5fd" stroke-width="1.4" opacity="0.55"/>
    <rect x="${bx}" y="${by}" width="${signw}" height="${signh}" rx="4" fill="#0d0820" stroke="#a855f7" stroke-width="1.3"/>
    <rect x="$((bx + 2))" y="$((by + 2))" width="$((signw - 4))" height="$((signh - 4))" rx="3" fill="none" stroke="#7c3aed" stroke-width="0.6" opacity="0.45"/>
    <image href="data:image/svg+xml;base64,${b64}" x="${ix}" y="${iy}" width="${icon}" height="${icon}"/>
  </g>
EOF
}

GITCITY_INNER=$(python3 << 'PY'
import re
text = open('/tmp/gitcity.svg').read()
inner = re.sub(r'^<svg[^>]*>', '', text)
inner = re.sub(r'</svg>\s*$', '', inner)
print(inner.strip())
PY
)

SIGNS_XML=""
for entry in "${SIGNS[@]}"; do
  IFS='|' read -r url gx gy style <<< "$entry"
  SIGNS_XML+=$(sign_svg "$url" "$gx" "$gy" "$style")
  SIGNS_XML+=$'\n'
done

cat > "$ASSETS/tech-skyline.svg" << EOF
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="800" height="340" viewBox="0 0 800 340" role="img" aria-label="GitCity skyline with tech billboard signs">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0a0618"/>
      <stop offset="100%" stop-color="#1a0f35"/>
    </linearGradient>
    <filter id="signGlow" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="1.8" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="800" height="340" fill="url(#sky)" rx="12"/>
  <text x="400" y="22" text-anchor="middle" fill="#c4b5fd" font-family="ui-monospace, Menlo, monospace" font-size="11" letter-spacing="0.12em">TECH DISTRICT · hannahpaterka</text>
  <g transform="translate(200, 38)">
${GITCITY_INNER}
  </g>
  <g transform="translate(200, 38)" filter="url(#signGlow)">
${SIGNS_XML}  </g>
  <text x="400" y="332" text-anchor="middle" fill="#6b6b78" font-family="ui-monospace, Menlo, monospace" font-size="9">neon signs on the skyline · click for 3D city</text>
</svg>
EOF

echo "Built $ASSETS/tech-skyline.svg ($(wc -c < "$ASSETS/tech-skyline.svg") bytes)"
