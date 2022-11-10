# Intro

This project uses:

- [Poetry](https://python-poetry.org/): for dependency management
- [FastAPI](https://fastapi.tiangolo.com/): as web framework
- [uvicorn](https://www.uvicorn.org/): as server program
- [pytest](https://pypi.org/project/pytest/): for unit testing
- [pytest-cov](https://pypi.org/project/pytest-cov/): for coverage report
- [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks) for pre-commit code check
- [black](https://github.com/psf/black) for pre-commit code formatting
- [prometheus_client](https://github.com/prometheus/client_python) and [prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator) for basic metrics

# Architecture

```
                                                        On POST file
                                                        BackgroundTasks: Read file stream chunk by chunk
                                                                         and write to local path
  POST /files/     ┌──────────────────────────┐            ▲             (Thread pool based)
────────────────►  │                          │            │           │
                   │    FastAPI backend       │            │           │
────────────────►  │                          ├────────────┘           │
  GET /files/<name>└──────────────────────────┘                        │
                                                                       │
                                                                       │
                                                                       ▼
                                                   ┌─────────────────────────────────┐
                                                   │                                 │
                                                   │                                 │
                                                   │   CephFileSystem (shared RWX)   │
                                                   │   managed by Rook Ceph Operator │
                                                   │                                 │
                                                   └─────────────────────────────────┘
```

endpoints

- /
  - GET a static html with a form and button
- /docs
  - GET auto generated doc
- /health
  - GET
- /files/
  - POST Content-Type: multipart/form-data
  - GET get a file by name /files/\<name\>

# Caveat

- authentication is not implemented

# Quick Start

## Dependencies Management:

This project use poetry for dependencies management.

- install poetry locally
  - refer to [offcial doc](https://python-poetry.org/docs/) or use the following command
    ```shell
    make install_poetry
    ```
- install all dependencies
  - ```shell
    make build_dep
    ```
- update all dependencies
  - ```shell
    make update_dep
    ```
- dump all dependencies as requirements.txt
  - ```shell
    make dump_dep
    ```

## Build Docker image:

- build dev image
  - ```shell
    make build_dev
    ```
- build test image (used for running unit test in a dedicated container)
  - ```shell
    make build_test
    ```
- build prod image
  - ```shell
    make build_prod
    ```

## Run Application:

- locally (no container)
  - ```shell
    make run_local
    ```
- in container
  - ```shell
    make run_prod  # run latest prod level image
    ```

## Run Tests

- locally (no container)
  - ```shell
    make test_local
    ```
- in container (build a test image first and then run it)
  - ```shell
    make test
    ```

# Deployment Guide

## Prerequsite

- loading kernel modules with all WSL Linux distributions is [not supported.](https://unix.stackexchange.com/questions/594470/wsl-2-does-not-have-lib-modules)
  - rbd module is required to run ceph, therefore please use other linux distribution or used hypervisors like hyperv, vmware etc.
- So this installation guide assumes that we are using **a standalone linux vm other than WSL with minikube, git pre-installed**.
- at least **3 devices** is required for rook-ceph to work on a single node minikube
  - you can achieve this with **--extra-disks=3** when using **--driver=hyperkit / --driver=kvm** , or otherwise:
    - using cloud server with block storage attached and mounted
    - use hypervisors like hyperv, vmware

## Deployment Example Procedure

Following example uses docker as minikube driver.

```shell
# use docker as driver
minikube start --driver=docker --disk-size=25g --extra-disks=3 --force

# check minikube ready or not
kubectl get nodes

# pull images in advance to save time
minikube ssh docker pull rook/ceph:v1.10.5
minikube ssh docker pull quay.io/ceph/ceph:v17
minikube ssh docker pull omelet034/simple-fs:latest

# clone rook repo and start deploy rook
git clone --single-branch --branch v1.10.5 https://github.com/rook/rook.git
cd rook/deploy/examples/

# create crds, operator and rook-ceph cluster for minikube
kubectl create -f crds.yaml -f common.yaml -f operator.yaml
kubectl -n rook-ceph create -f cluster-test.yaml

# watch and wait for all pods ready
kubectl get pods -n rook-ceph -w

# There should be at least 1 ceph-osd, ceph-mgr, ceph-mon running if installation proceeds smoothly
root@vultr:~/rook/deploy/examples# kubectl get pods -n rook-ceph
NAME                                            READY   STATUS      RESTARTS   AGE
csi-cephfsplugin-4jxrl                          2/2     Running     0          6m22s
csi-cephfsplugin-provisioner-75875b5887-54gxf   5/5     Running     0          6m22s
csi-rbdplugin-dvlhl                             2/2     Running     0          6m22s
csi-rbdplugin-provisioner-56d69f5d8-j4x77       5/5     Running     0          6m22s
rook-ceph-mgr-a-5b85749694-r46t2                1/1     Running     0          5m57s
rook-ceph-mon-a-75547cb9df-b6z69                1/1     Running     0          6m25s
rook-ceph-operator-64fb475fcb-f98rh             1/1     Running     0          6m36s
rook-ceph-osd-0-58fdf657db-7f4sw                1/1     Running     0          5m16s
rook-ceph-osd-1-86cc587864-6gwqc                1/1     Running     0          5m16s
rook-ceph-osd-prepare-minikube-l88s9            0/1     Completed   0          5m35s

# deploy rook-ceph toolbox and check ceph health status
root@vultr:~/rook/deploy/examples# kubectl create -f toolbox.yaml
deployment.apps/rook-ceph-tools created
root@vultr:~/rook/deploy/examples# kubectl -n rook-ceph rollout status deploy/rook-ceph-tools
deployment "rook-ceph-tools" successfully rolled out
root@vultr:~/rook/deploy/examples# kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- ceph status
  cluster:
    id:     05aac0da-b7b7-48ec-b39b-d6cc8c028525
    health: HEALTH_OK

  services:
    mon: 1 daemons, quorum a (age 7m)
    mgr: a(active, since 5m)
    osd: 2 osds: 2 up (since 6m), 2 in (since 6m)

  data:
    pools:   1 pools, 32 pgs
    objects: 2 objects, 463 KiB
    usage:   40 MiB used, 20 GiB / 20 GiB avail
    pgs:     32 active+clean


# create shared RWX CephFileSystem and wait for rook-ceph-mds-myfs running, create storage class
kubectl create -f filesystem-test.yaml
kubectl create -f csi/cephfs/storageclass.yaml

# deploy simplefs.yaml
root@vultr:~/rook/deploy/examples# kubectl create -f simplefs.yaml
persistentvolumeclaim/cephfs-pvc created
deployment.apps/simple-fs created
service/simple-fs created
root@vultr:~/rook/deploy/examples# kubectl get pods
NAME                        READY   STATUS    RESTARTS   AGE
simple-fs-d5cbb45c7-25h2d   1/1     Running   0          84s
root@vultr:~/rook/deploy/examples# kubectl get svc
NAME         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
kubernetes   ClusterIP   10.96.0.1       <none>        443/TCP          33m
simple-fs    NodePort    10.107.74.250   <none>        8080:30010/TCP   13s
root@vultr:~/rook/deploy/examples# kubectl get pvc -A
NAMESPACE   NAME         STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
default     cephfs-pvc   Bound    pvc-bed8b8d4-a143-4de0-8e95-8bac767ee532   1Gi        RWX            rook-cephfs    107s

# test connection
root@vultr:~/rook/deploy/examples# minikube service simple-fs
|-----------|-----------|-------------|---------------------------|
| NAMESPACE |   NAME    | TARGET PORT |            URL            |
|-----------|-----------|-------------|---------------------------|
| default   | simple-fs |        8080 | http://192.168.49.2:30010 |
|-----------|-----------|-------------|---------------------------|
🎉  Opening service default/simple-fs in default browser...
👉  http://192.168.49.2:30010

# check pvc mounted
root@vultr:~/rook/deploy/examples# kubectl exec pod/simple-fs-d5cbb45c7-25h2d -- df -h
Filesystem                                                                                                         Size  Used Avail Use% Mounted on
overlay                                                                                                             57G   16G   38G  30% /
tmpfs                                                                                                               64M     0   64M   0% /dev
10.107.214.86:6789:/volumes/csi/csi-vol-e02e9d6f-60fd-11ed-864d-0242ac110007/714e5586-219e-4110-94d9-058da2d8d778  1.0G     0  1.0G   0% /data

# run the test script k8s/test_client.py
python3 -m pip install requests
root@vultr:~# python3 test_client.py --url http://192.168.49.2:30010
input argument: url=http://192.168.49.2:30010
start testing ...
test finished! No errors output on screen means passed!
root@vultr:~#
```
