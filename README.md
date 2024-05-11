# Copado Jira Cloud Deployments Automation

## About the Extension

The **Copado Jira Cloud Deployments Automation** extension is designed to automate the process of notifying Jira Cloud with deployment information post-promotion using the [Jira Cloud Deployments API](https://developer.atlassian.com/cloud/jira/software/rest/api-group-deployments/). This extension enhances the integration between Copado and Jira Cloud by automatically updating Jira with the latest deployment status and details immediately after a promotion deployment is executed. This ensures that the project management and tracking systems are seamlessly synchronized with the actual deployment activities, improving visibility and traceability across development and operations teams. More details about the Jira Cloud deployments feature can be found [here](https://support.atlassian.com/jira-cloud-administration/docs/what-is-the-deployments-feature/).

## Setup

- a) Make sure your user has the following permission sets assigned: Copado User, Copado Job Engine, Copado Functions Admin
- b) Make sure your user has the Copado Admin license.
- c) Push the code and components in this repository to your Org.
- d) Go to Copado Extension Tab, select SampleExtensionBundle from dropdown.
- e) Click on Generate extension records
- f) Once your records have been generated, click on the "Hello World" Function to open the Function record
- g) On the Function record page, click Execute Function -> then Execute in the open modal
- h) Finally, click View result record in the next screen.
