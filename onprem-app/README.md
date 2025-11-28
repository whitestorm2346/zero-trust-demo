# On-Prem Zero Trust Demo (Step 1)

這個 demo 展示地端 Zero Trust 架構中的兩個關鍵身分政策：

- **Policy #4 - Service Identity**
  - Service-B 只接受來自被允許的 service (gateway) 的呼叫，且必須夾帶合法 service token
- **Policy #5 - Resource Authorization (Service + User Claims)**
  - Service-B 在 `/private` 端點會同時檢查：
    - 呼叫方 service 是否合法
    - user 的 role 是否符合條件（例：admin）

## 啟動方式

```bash
cd onprem-app
docker compose up -d --build
```
