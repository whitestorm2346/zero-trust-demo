**設定變數**

```bash
PROJECT_ID=zero-trust-demo-475103  \
REGION=asia-east1 \
ZONE=asia-east1-b \
REPO=gcp-app \
CLUSTER=zta-cluster \
ROUTER=gke-nat-router
```

**建立 GKE cluster（Cloud 原生環境）**

```bash
gcloud container clusters create $CLUSTER \
  --zone=$ZONE \
  --num-nodes=1 \
  --machine-type=e2-standard-2 \
  --disk-type=pd-standard \
  --disk-size=30


gcloud container clusters create $CLUSTER \
  --region $REGION \
  --release-channel regular \
  --num-nodes 2 \
  --machine-type e2-standard-4 \
  --disk-type=pd-standard \
  --disk-size=50 \
  --enable-ip-alias
```

**Install Istio**

```bash
istioctl install -y \
  --set profile=demo \
  --set revision=canary \
  --set components.cni.enabled=false
```

**取得 cluster 憑證 (讓本機可以使用 `kubectl apply`)**

```bash
gcloud container clusters get-credentials $CLUSTER --region $REGION --project=$PROJECT_ID
kubectl get nodes
```

看到節點列表就表示連線成功。

**建 Artifact Registry（放 image 用）**

```bash
gcloud artifacts repositories create $REPO \
  --repository-format=docker \
  --location=$REGION \
  --description="ZTA demo repo" || true

gcloud auth configure-docker $REGION-docker.pkg.dev -q
```

**Build & Push 兩個服務的 image**

```bash
# service-a
docker build --no-cache \
  -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/service-a:v1 gcp-app/service-a
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/service-a:v1

# service-b
docker build --no-cache \
  -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/service-b:v1 gcp-app/service-b
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/service-b:v1
```

**Set Image**

```bash
kubectl -n default set image deploy/service-a \
 app=$REGION-docker.pkg.dev/$PROJECT_ID/gcp-app/service-a:v1

kubectl -n default rollout status deploy/service-a

```

**安裝 Istio**

```bash
istioctl install -y \
  --set profile=demo \
  --set values.gateways.istio-ingressgateway.type=LoadBalancer \
  --set values.gateways.istio-egressgateway.enabled=true
```

**啟用 sidecar**

```bash
kubectl apply -f gcp-app/k8s/base/namespace.yaml
kubectl apply -f gcp-app/k8s/base/sa.yaml
kubectl apply -f gcp-app/k8s/istio/ns-injection.yaml
kubectl apply -f gcp-app/k8s/istio/peer-authn-mtls.yaml
```

**部署兩個 services**

```bash
kubectl apply -f gcp-app/k8s/base/svc-b.yaml
kubectl apply -f gcp-app/k8s/base/svc-a.yaml

kubectl rollout restart deploy/service-b
kubectl rollout restart deploy/service-a

kubectl delete pod -n default -l app=service-a
kubectl delete pod -n default -l app=service-b
kubectl get pods
```

應該會看到兩個 Pod 都是 `2/2 READY`（代表 sidecar 已注入）。

**建立 JWT 驗證**

```bash
kubectl apply -f gcp-app/k8s/istio/request-authn-jwt.yaml

kubectl get requestauthentication -A
kubectl delete requestauthentication jwt-auth -n default

```

**建立 AuthorizationPolicy**

```bash
kubectl apply -f gcp-app/k8s/istio/authz-service-a-public.yaml
kubectl apply -f gcp-app/k8s/istio/authz-service-a-private-admin.yaml
kubectl apply -f gcp-app/k8s/istio/authz-egress.yaml

kubectl get authorizationpolicy -n default
kubectl get authorizationpolicy -A
```

**建立 ingress**

```bash
kubectl apply -f gcp-app/k8s/istio/gateway.yaml
kubectl apply -f gcp-app/k8s/istio/virtualservice.yaml

kubectl get svc -n istio-system istio-ingressgateway
kubectl get svc -n istio-system istio-ingressgateway -o wide

```

複製 `EXTERNAL-IP` 記下來，用來測試網站。

**啟用 KeyCloak**

```bash
kubectl apply -f gcp-app/k8s/keycloak/namespace.yaml
kubectl apply -f gcp-app/k8s/keycloak/keycloak.yaml
kubectl apply -f gcp-app/k8s/keycloak/deployment.yaml
kubectl apply -f gcp-app/k8s/keycloak/service.yaml

kubectl get pod -n keycloak

kubectl port-forward -n keycloak deploy/keycloak 8080:8080
kubectl port-forward pod/keycloak-7d875f74c5-fljdz 18080:8080
```

**建立 egress**

```bash
kubectl apply -f gcp-app/k8s/istio/egress-gateway.yaml
kubectl apply -f gcp-app/k8s/istio/egress-serviceentry.yaml
kubectl apply -f gcp-app/k8s/istio/egress-virtualservice.yaml
```

**套用 Identity-tier Policy（加強側邊安全）**

```bash
kubectl apply -f gcp-app/k8s/istio/authz-identity.yaml
```

**清理 節省費用**

```bash
kubectl delete -f gcp-app/k8s/istio/ingress-a.yaml
gcloud container clusters delete $CLUSTER --zone=$ZONE --project=$PROJECT_ID
```

**網頁測試**

```txt
http://35.201.249.209/
```

**CURL 測試**

```bash
kubectl run curlpod --image=curlimages/curl -it --rm -- sh

curl -v http://service-b:8080/public    # 要 200
curl -v http://service-b:8080/private   # 要 403
```

**建立 Cloud Router**

```bash
gcloud compute routers create gke-nat-router \
  --network=default \
  --region=$REGION
```

**建立 Cloud NAT 設定**

```bash
gcloud compute routers nats create nat-config \
  --router=$ROUTER \
  --router-region=$REGION \
  --nat-all-subnet-ip-ranges \
  --auto-allocate-nat-external-ips
```
