# Copado Jira Cloud Deployments Automation

## About the Extension

The **Copado Jira Cloud Deployments Automation** extension is designed to automate the process of notifying Jira Cloud with deployment information post-promotion using the [Jira Cloud Deployments API](https://developer.atlassian.com/cloud/jira/software/rest/api-group-deployments/). This extension enhances the integration between Copado and Jira Cloud by automatically updating Jira with the latest deployment status and details immediately after a promotion deployment is executed. This ensures that the project management and tracking systems are seamlessly synchronized with the actual deployment activities, improving visibility and traceability across development and operations teams. More details about the Jira Cloud deployments feature can be found [here](https://support.atlassian.com/jira-cloud-administration/docs/what-is-the-deployments-feature/).

## Prerequisities

- Install Copado v22.22 or higher
- Install Copado Connect v4.35 or higher
- Install Copado Jira Cloud Deployments Automation Extension

## Considerations & Limitations

- Supported only for Salesforce Source Format Pipelines
- Supported only for **Immediate** exeuction time of Automations.  **Scheduled** execution is not yet supported.
- Works with Jira issues associated within User Story Bundles included in Promotion Deployment
- Limit of 5,000 Jira issues per Promotion Deployment

## Setup

### Jira Cloud Setup
Please work with your Jira admin to enable the following settings.

#### Create OAuth Credentials within Jira Admin Console ([more info](https://support.atlassian.com/jira-cloud-administration/docs/integrate-with-self-hosted-tools-using-oauth/))

1. Login to your Jira Cloud instance and select Settings (gear icon)  > Apps.
2. From the sidebar, select **OAuth credentials**.
3. Select **Create credentials**.
4. Enter the following details and click **Create**:
    - App name: `Copado`
    - Server base URL: `<your Copado org URL e.g. https://copado.my.salesforce.com/>`
    - Logo URL: `https://assets-global.website-files.com/62d8507d84c54d359ad063bc/62f562c6eb37c731230c6837_favicon.png` (Copado favicon)
    - Permissions: `Deployments`

#### Enable Deployments within Jira Project(s) ([more info](https://support.atlassian.com/jira-software-cloud/docs/enable-deployments/))
*You must be a project admin to enable and disable features on a project. You must also have the permission View Development Tools to enable the Deployments feature.*
1. Navigate to your software project.
2. Go to **Project Settings > Features**.
3. Enable the **Deployments** feature.

A new menu item, **Deployments**, will be added to the project menu.

### Copado Setup

#### Permission Set Configuration & Assignment
- Ensure that all Copado Users and Admins have been granted access to the following Apex Classes:
  - `JiraCloudDeploymentsConnector`
  - `JiraCloudDeploymentsConnectorTest`
- All **Copado User** licensed users require the following Permission Set(s):
  - `Execute Automations`
- All **Copado Admin** licensed users require the following Permission Set(s):
  - `Configure Automations`

#### Generate Extensions Records ([more info](https://docs.copado.com/articles/#!copado-ci-cd-publication/upgrade-to-a-new-version-of-an-extension-package-2/))
1. Install the latest version of the Jira Cloud Deployments Automation extension package found on the [Copado DevOps Exchange](https://success.copado.com/s/exchange-search).
2. Once the installation is complete, navigate to the **Copado Extensions** tab and select `JiraDeploymentsExtension` in the **Select Extension** drop-down menu.
3. Copado will display a list of all the records included in the package. A check will be displayed next to the record name if the records have not changed. On the contrary, if the record has been updated in the new version or if you have customized it, a cross will appear.  If needed, you can click **View Differences** on the drop-down menu to review the changes.
4. Click **Generate Extension Records** button to generate the necessary Job Template and Function records.

#### Create Pipeline System Properties


#### Create Environment System Properties

#### Configure Automation