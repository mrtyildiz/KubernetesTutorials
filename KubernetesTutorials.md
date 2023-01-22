## Kubernetes Notları

### Kubernetes için kullanılabilecek lablar

- Play Kubernetes
- killerkoda
- killer.sh

### Kubernetes Konular;

- Etcd backup
- Kubeadm master upgrade
- Network policy
- Sidecar container
- Init Container
- pv, pvc, using pod
- pvc size increase
- Log Busybox
- Kubernetes node kubelet problem
- Kubernetes node drain
- Nodeselector
- How many nodes
- Create nodeport services
- Multi Container
- Pod logs grep
- Scale deployment
- Clusterrole, Clusterrole binding

Not önemli Play'de çalışırken
COPY -> CTRL+INSERT or CTRL+FN+INSERT
PASTE -> SHIFT+CTRL+V

```
### Kısaltma kullanılması 
Get resources

alias k=”kubectl”
alias kn=”kubectl get nodes -o wide”
alias kp=”kubectl get pods -o wide”
alias kd=”kubectl get deployment -o wide”
alias ks=”kubectl get svc -o wide”

Describe K8S resources

alias kdp=”kubectl describe pod”
alias kdd=”kubectl describe deployment”
alias kds=”kubectl describe service”
alias kdn=”kubectl describe node”

Yukarıdaki komutları kısaltmalar için kullanılmaktadır bu sayede daha hızlı bir şekilde komutları kullanabiliriz.
```

kubectl run simple-pod --image=nginx --dry-run=client -o yaml > simple.yaml
Bu komut ile simple bir yaml yazılabilir.

kubectl run --image=busybox --command sleep 3600 --dry-run=client -o yaml > busy.yaml
busy image içerisinde network komutları kullanılması amacıyla kullanılan imajdır.
Bu imaj üzerinde çalışan bir servis veya komut olmadığı için silinir. Bu yüzden --command kullanılır.

```
kubeadm init --apiserver-advertise-address $(hostname -i) --pod-network-cidr 10.5.0.0/16

kubectl apply -f https://raw.githubusercontent.com/cloudnativelabs/kube-router/master/daemonset/kubeadm-kuberouter.yaml

kubectl apply -f https://raw.githubusercontent.com/kubernetes/website/master/content/en/examples/application/nginx-app.yaml
```
Kopya yeri kesin kullan
https://kubernetes.io/docs/reference/kubectl/cheatsheet/


### Kubeadm ile Kubernetes Cluster Kurma & Upgrade Etme

Ortamın kurulması amacıyla bir node bir master olacak şekilde iki adet makinemiz bulunmaktadır.
İki makineyede yapılacak işlemler aşağıdaki gibidir;

- sudo su -
- apt-get update
- apt-get install containerd -y
- mkdir -p /etc/containerd
- containerd config default /etc/containerd/config.toml
- sudo systemctl restart containerd
- sudo systemctl enable containerd

#### sys
- sudo modprobe overlay
- sudo modprobe br_netfilter
- sudo nano /etc/sysctl.d/kubernetes.conf
```
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
```
- sudo sysctl --system

### kubeadm, kubelet, kubectl Kurulumu

- curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
- sudo apt-add-repository "deb http://apt.kubernetes.io/ kubernetes-xenial main"
- apt-cache madison kubeadm // mevcut versiyonları görme.
- apt-get install kubeadm=1.24.2-00 kubelet=1.24.2-00 kubectl=1.24.2-00 -y

### Master Node Oluşturulması 
- sudo kubeadm config images pull
- sudo kubeadm init --pod-network-cidr=10.100.0.0/16

*** Burada hata alınması durumunda aşağıdaki komutu çalıştırıp yeniden init etmeyi deneyin
```
mv /etc/kubernetes/manifests/kube-apiserver.yaml \
/etc/kubernetes/manifests/kube-controller-manager.yaml \
/etc/kubernetes/manifests/kube-scheduler.yaml \
/etc/kubernetes/manifests/etcd.yaml ./
```
İşlemler sıralı bir şekilde gerçekleşmelidir.

https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/


## kubernetes etcd backup almak ve restore etmek
### ETCD Backup

- kubectl get pods -n kube-system
- kubectl describe pod kube-apiserver-node1 -n kube-system //buradan sertifika yolunun bilgini alacağız


ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/apiserver-etcd-client.crt --key=/etc/kubernetes/pki/apiserver-etcd-client.key snapshot save /tmp/backup.db

### ETCD Restore

- mkdir -p /var/etcd
- ETCDCTL_API=3 etcdctl snapshot restore --data-dir /var/etcd /tmp/backup.db


--etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt
      --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt
      --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key



### multi container nedir, sidecar container

İlk öncelikle bir basit bir yaml dosyası oluşturulması gerekmektedir;
- kubectl run multi --image=nginx --dry-run=client -o yaml > multi.yaml

Oluşturulmuş olan yaml dosyasını düzenlendikten sonra (sonda bulunan üç satır sil)
yeni bir image eklenmelidir.
``
apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: null
  labels:
    run: multi
  name: multi
spec:
  containers:
  - image: nginx
    name: nginx
  - image: redis
    name: redis
``
kubectl log multi -c nginx \\ ile nginx cihazın loglarını 
kubectl log multi -c redis \\ ile redis 'in loglarını görebilirsiniz.


sidecar - işlemi

sidecar.yaml
```
apiVersion: v1
kind: Pod
metadata:
  name: multi-container
  labels:
    app: multi
spec:
  containers:
  - image: nginx
    name: main-container
    ports:
      - containerPort: 80
    volumeMounts:
    - name: var-logs
      mountPath: /usr/share/nginx/html
  - image: busybox
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo echo $(date -u) 'Hi I am from Sidecar container' >> /var/log/index.html; sleep 5;done"]
    name: sidecar-container
    volumeMounts:
    - name: var-logs
      mountPath: /var/log
  volumes:
  - name: var-logs
    emptyDir: {}
```
Buradaki temel amac iki farklı container 'da bulunan iki adet path birbirine mount etmektir. 
main-container 'ın /usr/share/nginx/html dizini ile  sidecar-container pod 'unda bulunan /var/log dizinidir.

Node üzerinde bulunan port üzerinden erişimin sağlanması amacıyla;
- kubectl expose pod multi-container --port 80 --type NodePort

Nodeların kendi IP adresinin görüntülenmesi amacıyla;
- kubectl get nodes -o wide

Oluşturulmuş olan service ait atanmış port'un görüntülenmesi amacıyla;
- kubectl get svc -o wide


### persistentvolume, persistentvolumeclaim, pv ve pvc nedir

Persistence pod oluşturulması ve kullanılmasına yönelik uygulama adımları aşağıdaki gibidir;
İlk olarak "kubectl get nodes" komutu kullanılarak nodelar görüntülenir. worker node'na ssh ile bağlanılır.
Bağlanılan node 'da "/mnt/data" dizini oluşturulur

```
controlplane $ kubectl get node
NAME           STATUS   ROLES           AGE   VERSION
controlplane   Ready    control-plane   24d   v1.26.0
node01         Ready    <none>          24d   v1.26.0
controlplane $ ssh node01
Last login: Sun Nov 13 17:27:09 2022 from 10.48.0.33
node01 $ sudo mkdir /mnt/data
node01 $ sudo sh -c "echo 'Hello from Kubernetes storage' > /mnt/data/index.html"
```
Master nodena geri dönülmesi amacıyla "exit" komutu kullanılır. "nano pv.yaml" komutu kullanılarak içerisine;
```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-pv
  labels:
    type: local
spec:
  storageClassName: manual
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
```

"nano pvc.yaml" komutu kullanılarak;
```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
  namespace: web
spec:
  storageClassName: manual
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 3Gi
```

Yukarıda da görüldüğü gibi web adlı bir namespace kullanılmıştır. Bu namespace oluşturulması adına "kubectl create namespace web" komutu kullanılır. Sırasıyla aşağıdaki komutlar kullanılır;

- kubectl apply -f pv.yaml // volumun ve path belirtilir.
- kubectl apply -f pvc.yaml // yetkilendirme islemi ve namespace oluşturulur.
- kubectl get pv // volumes görüntülenmesi işlemi gerçekleştirilir.
```
controlplane $ kubectl apply -f pv.yaml 
persistentvolume/my-pv created
controlplane $ kubectl get pv
NAME    CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM   STORAGECLASS   REASON   AGE
my-pv   10Gi       RWO            Retain           Available           manual                  7s
controlplane $ kubectl apply -f pvc.yaml.yaml 
error: the path "pvc.yaml.yaml" does not exist
controlplane $ kubectl apply -f pvc.yaml      
persistentvolumeclaim/my-pvc created
controlplane $ kubectl get pv
NAME    CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM        STORAGECLASS   REASON   AGE
my-pv   10Gi       RWO            Retain           Bound    web/my-pvc   manual                  22s
controlplane $ 
```
Volume ile ilgili işlemlerden sonra pod 'un oluşturrulması amacıyla pod.yaml dosya;
```
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  namespace: web
  labels:
    app: web
spec:
  volumes:
    - name: volume
      persistentVolumeClaim:
        claimName: my-pvc
  containers:
    - name: task-pv-container
      image: nginx
      ports:
        - containerPort: 80
          name: "http-server"
      volumeMounts:
        - mountPath: "/usr/share/nginx/html"
          name: volume
```
pod 'un oluşturulması amacıyla "kubectl apply -f pod.yaml" komutu kullanılır. Oluşturulan pod'un port açma işlemi için "kubectl expose pod my-pod -n web --port 80 --type NodePort" oluşturulan servisin görüntülenmesi amacıyla "kubectl get svc -n web" komutu kullanılır.

```
controlplane $ kubectl get pod -n web
NAME     READY   STATUS    RESTARTS   AGE
my-pod   1/1     Running   0          5m13s
controlplane $ kubectl get pod -n web --show-labels
NAME     READY   STATUS    RESTARTS   AGE     LABELS
my-pod   1/1     Running   0          5m15s   app=web
controlplane $ kubectl expose pod my-pod -n web --port 80 --type NodePort
service/my-pod exposed
controlplane $ kubectl get svc -n web
NAME     TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
my-pod   NodePort   10.110.25.99   <none>        80:32606/TCP   19s
controlplane $ kubectl get node -o wide
NAME           STATUS   ROLES           AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION      CONTAINER-RUNTIME
controlplane   Ready    control-plane   24d   v1.26.0   172.30.1.2    <none>        Ubuntu 20.04.5 LTS   5.4.0-131-generic   containerd://1.6.12
node01         Ready    <none>          24d   v1.26.0   172.30.2.2    <none>        Ubuntu 20.04.5 LTS   5.4.0-131-generic   containerd://1.6.12
controlplane $ curl http://172.30.2.2:32606
Hello from Kubernetes storage
controlplane $ 
```
nodelarda bulunan IP adreslerinin görüntülenmesi amacıyla "kubectl get node -o wide" komutu kullanılır ve curl isteği atılır.
https://kubernetes.io/docs/tasks/configure-pod-container/configure-persistent-volume-storage/



### Kubernetes Service Türleri: ClusterIP, NodePort, Loadbalancer

Servis türleri kullanılarak işlemlerinin gerçekleştirilmesi;
#### ClusterIP
İlk öncelikle nginx üzerinde bir pod üzerinde çalıştırılması amacıyla;
- kubectl run web --image=nginx
Çalışan pod durumunun görüntülenmesi amacıyla;
- kubectl get pods

Oluşturulmuş olan pod 'un dışarı açılması amacıyla;
- kubectl expose pod web2 --port=80
- kubectl get svc

İkinci bir pod oluşturulması amacıyla;
- kubectl run busy --image=busybox --command sleep 3600
- kubectl get pods
- kubectl get svc
- kubectl exec -ti busy -- sh
- wget http://<web-Cluster-IP>
- cat index.html

#### NodePort

İkinci bir pod oluşturulması amacıyla;
- kubectl run web3 --image=nginx
NodePort 'un oluşturulması;
- kubectl expose pod web3 --port 80 --type NodePort

Bu İşlemlerin ardından nodes ve podlar görüntülenmesi amacıyla;
- kubectl get pods
- kubectl get nodes
- curl http://<External-IP>:<NodePort>

#### LoadBalancer

yeni podlar oluşturulması amacıyla;
- kubectl run web3 --image=nginx
- kubectl expose web3 --port 80 --type LoadBalancer // IP gelene kadar bekle 
- kubectl get svc /// oluşturulan IP adresine 80 portu üzerinden ulaşılabilir durumdadır.


### Network 

İlk öncelikle iki farklı namespace oluşturulması;
- kubectl create ns a
- kubectl create ns b

Bu namespacelere ait podlar oluşturulması;
- kubectl run pod-a -n a --image=busybox --command sleep 3600
- kubectl run pod-b -n b --image=busybox --command sleep 3600

Oluşturulan podların görüntülenmesi;
- kubectl get pods --all-namespace -o wide | grep pod-

Podların IP adreslerinin görüntülenmesi amacıyla;
- cat /etc/kubernetes/mainfests/kube-controller-manager.yaml | grep --cluster-cidr

Podlar oluşturulduktan sonra podlar içerisinden ping işlemini gerçekleştiriniz.
Bunun için podlara exec olmak gerekmetedir.!!!

Oluşturulmuş olan podlara Label verme işlemi;
- kubectl label pod pod-a -n a app=busy1
- kubectl label pod pod-b -n b app=busy2


Network üzerinde bütün podlara erişim izin verilmez;
- nano np1.yaml
```
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: np1
  namespace: b
spec:
  podSelector: {}
  policyTypes:
    - Ingress
```

- kubectl apply -f np1.yaml
- kubectl get pods -n a
- kubectl exec -ti -n a pod-a -- sh
- ping //atma işlemi

Network üzerinde bütün podlara erişim izin verilmesi;
- nano np2.yaml
```
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: np1
  namespace: b
spec:
  podSelector: {}
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: a
```
- kubectl delete -f np1.yaml
- kubectl apply -f np2.yaml
- kubectl exec -ti -n a pod-a -- sh

Kesinlikle bak network için;
https://github.com/ahmetb/kubernetes-network-policy-recipes


#### ingress nedir, nginx ingress configurasyonu

Örneği aşağıdaki gibidir;

- minikube start
- minikube addons list
- minikube addons enable ingress
- kubectl get ns
- kubectl get all -n ingress-nginx
- kubectl run web1 --image=nginx
- kubectl run web2 --image=httpd
- kubectl get pods
- kubectl expose pod web1 --port=80
- kubectl expose pod web2 --port=80
- kubectl get svc

- kubectl apply -f example-ingress.yaml
----
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$1
spec:
  rules:
  - host: devopsdude.info
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web1
            port:
              number: 80
      - path: /login
        pathType: Prefix
        backend:
          service:
            name: web2
            port:
              number: 80
------

- kubectl get ingress
- sudo nano /etc/hosts
- minikube ip 
- kubectl get nodes -o wide
- kubectl get svc -n ingress-nginx
- kubectl get ingress
- kubectl describe ingress web

###  NodeName, NodeSelector, Static-Pod

- cat kind.yaml
''''
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpho4
networking:
  apiServerAddress: "127.0.0.1"
  apiServerPort: 6443
nodes:
- role: control-plane
- role: worker
- role: worker
'''''''''''''''''''''

- kind create cluster --name cka --config kind.yaml
- kubectl cluster-info --context kind-cka
- kubectl get nodes
- kubectl run simple --image=nginx --dry-run=client -o yaml
- kubectl run simple --image=nginx --dry-run=client -o yaml > simple.yaml
- cat simple.yaml

''''
apiVersion: v1
kind: Pod
metadata:
  labels:
    run: nodename-pod
  name: nodename-pod
spec:
  containers:
  - image: nginx
    name: simple
  nodeName: cka-worker
''''

- kubectl apply -f simple.yaml
- kubectl get pods -o wide

- cat simple.yaml

''''
apiVersion: v1
kind: Pod
metadata:
  labels:
    run: nodename-pod-2
  name: nodename-pod-2
spec:
  containers:
  - image: nginx
    name: simple
  nodeName: cka-worker
''''

- kubectl apply -f simple.yaml
- kubectl get pods -o wide

### static pods
- kubectl get pods -n kube-system
- docker ps
- docker exec -it cka-control-plane /bin/bash
- ls /etc/kubernetes/manifests/
- docker cp static-pod.yaml cka-worker2:/etc/kubernetes/manifests/
'''
apiVersion: v1
kind: Pod
metadata:
  name: static-pod
spec:
  containers:
  - image: nginx
    name: nginx
'''
- kubectl get pods -o wide


### NodeSelector

- kubectl get nodes --show-labels
- nano simple.yaml
''''
apiVersion: v1
kind: Pod
metadata:
  labels:
    run: nodeselector-pod
  name: nodeselector-pod
spec:
  containers:
  - image: nginx
    name: nginx
  nodeSelector:
    node: highcpu
''''
- kubectl get nodes
- kubectl get pods
- kubectl get pods -o wide
- kubectl label node cka-worker2 node=highcpu
- kubectl get nodes --show-labels
- kubectl apply -f simple.yaml
- kubectl get pods -o wide
/// Edit
simple.yaml
''''
apiVersion: v1
kind: Pod
metadata:
  labels:
    run: nodeselector-pod-2
  name: nodeselector-pod-2
spec:
  containers:
  - image: nginx
    name: nginx
  nodeSelector:
    node: highcpu
''''
- kubectl apply -f simple.yaml
- kubectl get -o wide
/// Edit
simple.yaml
''''
apiVersion: v1
kind: Pod
metadata:
  labels:
    run: nodeselector-pod-3
  name: nodeselector-pod-3
spec:
  containers:
  - image: nginx
    name: nginx
  nodeSelector:
    node: backend
''''
- kubectl apply -f simple.yaml
- kubectl get pods -o wide
- kubectl describe pod nodeselector-pod-3 // pending durumunda olacak bu durumun nedeni öğren
- kubectl get pods -o wide
- kubectl label node cka-worker app=backend
- kubectl get pods -o wide


#### RBAC nedir, Role Based Access Control ile kubernetes auth

- kubectl get nodes
- kubectl create ns web
- kubectl get sa
- kubectl get sa -n web
- kubectl run web --image=nginx
- kubectl get pods
- kubectl describe sa web
- kubectl exec -it web -- bash
- ls /var/run/secrets/kubernetes.io/serviceaccount
- cat /var/run/secrets/kubernetes.io/serviceaccoun/token
- exit

- kubectl create sa get-sa -n web
- nano get-role.yaml
''''
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: web
  name: get-role
rules:
- apiGroups: [""] # "" indicates the core API group
  resources: ["pods", "services"]
  verbs: ["get"]
''''
- kubectl create -f get-role.yaml
- kubectl get role -n web
- kubectl create rolebinding get-binding --clusterrole=get-role --serviceaccount=web:get-sa --namespace=web
- kubectl get sa,roleirolebinding -n web
- kubectl auth can-i delete deployment --namespace web --as system:serviceaccount:web:get-sa
- kubectl auth can-i create pvc --namespace web --as system:serviceaccount:web:get-sa
- kubectl auth can-i get pods --namespace web --as system:serviceaccount:web:get-sa
- kubectl auth can-i get services --namespace web --as system:serviceaccount:web:get-sa
