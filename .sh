repomix --no-file-summary --no-security-check \
    --include "src/**" --output "repopack.yml"

pip install --no-cache-dir -r requirements.txt

docker run -d   --name xx-2   --label "traefik.http.routers.test.rule=Host(\`xx-2.dublok.com\`)"   nginx:latest

export CLOUDFLARE_EMAIL=""
export CLOUDFLARE_API_KEY=""
export HARBORDNS_TARGET="x.dublok.com"
export HARBORDNS_TYPE="CNAME"