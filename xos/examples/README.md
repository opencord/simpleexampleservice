The following describes a demo that brings up a `SimpleExampleServiceInstance`. The purpose of this ServiceInstance is to host a single web inside of a Kubernetes container. Creating the `SimpleExampleServiceInstance` will cause a model policy to be invoked, which will create the necessary Kubernetes resources to launch the web server and configure it to host the desired page.

1. Set your username and password

    USERNAME=admin@opencord.org
    PASSWORD=letmein

2. Run the TOSCA recipe

    TOSCA_URL=$(minikube service xos-tosca --url)
    curl -H "xos-username: $ACCOUNT" -H "xos-password: $PASSWORD" -X POST --data-binary @$RECIPE $TOSCA_URL/run    

3. Wait a few seconds for the Kubernetes instances to be created.

4. View the status

    CHAMELEON_URL=$(minikube service xos-chameleon --url)
    python ./show-instances.py $CHAMELEON_URL $USERNAME $PASSWORD

5. View the web page
Enter one of the other Kubernetes containers, any container such as one of the synchronizer containers will do, and perform a curl on the IP address obtained in step 4.