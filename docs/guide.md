# Docker build and push instructions
# PowerShell (Windows)

> Run these in the repo root.

**1) Create a tag and push it (optional if you’re not using GitHub Actions):**

```powershell
git tag v0.1.0
git push --tags
```

**2) Log in to GHCR:**

```powershell
$env:GHCR_USER="knowusuboaky"
$env:GHCR_TOKEN="<YOUR_GHCR_PAT>"   # scopes: read:packages, write:packages
$env:GHCR_TOKEN | docker login ghcr.io -u $env:GHCR_USER --password-stdin
```

**3) Ensure a Buildx builder exists and select it:**

```powershell
$BUILDER = "chromadb_builder"

if (-not (docker buildx ls | Select-String -Quiet "\b$BUILDER\b")) {
  docker buildx create --name $BUILDER --use | Out-Null
} else {
  docker buildx use $BUILDER
}
```

**4) Build multi-arch (amd64 + arm64) and PUSH to GHCR (CPU image):**

```powershell
$IMAGE="ghcr.io/knowusuboaky/chromadb"

docker buildx build `
  -f Dockerfile `
  --platform linux/amd64,linux/arm64 `
  -t $IMAGE`:0.1.0 `
  -t $IMAGE`:latest `
  --push `
  .
```

**(Optional) 5) Build & push a CUDA tag:**

```powershell
$IMAGE="ghcr.io/knowusuboaky/chromadb"

docker buildx build `
  -f Dockerfile `
  --build-arg TORCH_INDEX_URL=https://download.pytorch.org/whl/cu121 `
  --platform linux/amd64 `
  -t $IMAGE`:cuda-0.1.0 `
  -t $IMAGE`:cuda `
  --push `
  .
```