Terraform – AWS VPC + EKS
=========================

What `terraform apply` builds in `ap-south-1` (Mumbai):

```mermaid
flowchart TB
    subgraph VPC["VPC 10.30.0.0/16"]
        subgraph PUB["public subnets (2 AZs)"]
            NAT["NAT gateway"]
            ELB["load balancer<br/>(created later by ingress-nginx)"]
        end
        subgraph PRIV["private subnets (2 AZs)"]
            N1["node t3.medium"]
            N2["node t3.medium"]
        end
    end
    CP["EKS control plane<br/>(API reachable only from api_allowed_cidrs)"] --- N1 & N2
    N1 & N2 -->|"image pulls"| NAT --> IGW["internet gateway"]
```

| File | Contents |
|---|---|
| `versions.tf` | Terraform ≥ 1.7, AWS provider 5.x (required by the EKS module 20.x) |
| `provider.tf` | region + default tags (`Project=foundit`) on every resource |
| `variables.tf` | region, names, versions, node size/count, **`api_allowed_cidrs` (required)** |
| `main.tf` | VPC module, EKS module (+ addons: vpc-cni, coredns, kube-proxy, EBS CSI, metrics-server), IRSA role for EBS CSI |
| `outputs.tf` | cluster name/endpoint, VPC + subnet IDs, NAT IP, the `aws eks update-kubeconfig` command |
| `terraform.tfvars.example` | copy to `terraform.tfvars` (git-ignored) |

## Cost

These are rough on-demand prices for ap-south-1. Check the AWS pricing pages before you start.

| Resource | ≈ per hour |
|---|---|
| EKS control plane | $0.10 |
| 2 × t3.medium | $0.09 |
| NAT gateway (+ data) | $0.06 |
| load balancer (ingress-nginx) | $0.03 |
| **total** | **≈ $0.30/hour → under $1 for a 2-hour window** |

Not destroying it costs about $7 per day. Set an AWS Budget alert before you `apply`.

## The AWS window, in order

```bash
cp terraform.tfvars.example terraform.tfvars      # then set api_allowed_cidrs to YOUR_IP/32
terraform init
terraform validate
terraform plan -out tfplan                          # screenshot (M7)
terraform apply tfplan                              # ~15-20 min

aws eks update-kubeconfig --region ap-south-1 --name foundit-eks
kubectl get nodes

helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace --wait
kubectl apply -f ../k8s/namespace.yaml
helm upgrade --install foundit ../helm/foundit -n foundit \
  -f ../helm/foundit/values-eks.yaml -f ../helm/foundit/values-image.yaml --wait
kubectl get svc -n ingress-nginx ingress-nginx-controller   # EXTERNAL-IP = the ELB hostname → open it
```

## Teardown, in this order

The load balancer and the EBS volume are created **by Kubernetes**, not by Terraform. If they still
exist, `terraform destroy` hangs on the VPC: the ELB's network interfaces keep the subnets in use.

```bash
helm uninstall foundit -n foundit
kubectl delete pvc --all -n foundit          # the PVC is kept on uninstall on purpose - delete it here
helm uninstall ingress-nginx -n ingress-nginx
kubectl get svc -A | grep LoadBalancer       # must print nothing before you continue
terraform destroy                            # screenshot (M7)
```

Then check in the AWS Console (ap-south-1) that none of these are left: EKS clusters, EC2 instances,
NAT gateways, Elastic IPs, load balancers, EBS volumes, VPCs named `foundit-eks-vpc`.
The KMS key the EKS module created stays in "pending deletion" for 7 days. That's normal, and it
costs at most a few cents.
