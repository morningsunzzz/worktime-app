# 部署指南

## 服务器准备

### 1. 安装 PostgreSQL（不在 K3s 里）
```bash
apt install -y postgresql-16
su - postgres
psql -c "CREATE DATABASE worktime;"
psql -c "CREATE USER worktime WITH ENCRYPTED PASSWORD 'worktime123';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE worktime TO worktime;"
```

### 2. 建表
```sql
-- 连接 worktime 数据库后执行
CREATE TABLE work_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL UNIQUE,
    clock_in TIMESTAMP NOT NULL,
    clock_out TIMESTAMP,
    total_hours DECIMAL(4,2),
    overtime_hours DECIMAL(4,2),
    note TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    standard_hours DECIMAL(4,2) DEFAULT 8,
    lunch_break_minutes INTEGER DEFAULT 60,
    pre_hours DECIMAL(4,2) DEFAULT 1
);

INSERT INTO settings (id, standard_hours, lunch_break_minutes, pre_hours)
VALUES (1, 8, 60, 1);
```

## 构建和部署

```bash
# 构建镜像
docker build -t <your-registry>/worktime-backend:latest ./backend
docker build -t <your-registry>/worktime-frontend:latest ./frontend

# push 到 registry
docker push <your-registry>/worktime-backend:latest
docker push <your-registry>/worktime-frontend:latest

# 安装 Helm Chart（修改 values.yaml 里的 server-ip 和 registry）
helm install worktime ./helm/worktime

# 验证
kubectl get pods
kubectl get svc

# 手机访问 http://<server-ip>:30080
```
