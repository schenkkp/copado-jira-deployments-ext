global with sharing class JiraCloudDeploymentsConnector extends copado.AutomationConnector {

    private copado.CreateExecution.Request jobTemplateRequest;

    @TestVisible private static String templateName = 'Jira_Deployment_Notification_1'; //API Name of the Job Template

    global override List<copado.AutomationConnector> getConnectors(copado.AutomationConnectorContext context) {

        copado__Automation_Event__c aEvent = [SELECT Id, copado__Job_Execution_Id__c FROM copado__Automation_Event__c WHERE Id = :context.automationEvents[0].Id];
       
        copado__JobExecution__c je = [SELECT Id, copado__Deployment__r.copado__Promotion__c, copado__Deployment__r.copado__Promotion__r.copado__Project__r.copado__Deployment_Flow__c, copado__Deployment__r.copado__Promotion__r.copado__Destination_Environment__c, copado__DataJson__c FROM copado__JobExecution__c WHERE Id = :aEvent.copado__Job_Execution_Id__c];
       
        // Deserialize the JSON string into a map
        Map<String, Object> json = (Map<String, Object>) JSON.deserializeUntyped(je.copado__DataJson__c);

        // Access the deploymentDryRun variable from the map
        Boolean deploymentDryRun = (Boolean) json.get('deploymentDryRun');

        if(deploymentDryRun) {
            return null;
        } else {
            jobTemplateRequest = new copado.CreateExecution.Request();
            jobTemplateRequest.parentId = je.copado__Deployment__r.copado__Promotion__c;
            jobTemplateRequest.pipelineId = je.copado__Deployment__r.copado__Promotion__r.copado__Project__r.copado__Deployment_Flow__c;
            jobTemplateRequest.destinationId = je.copado__Deployment__r.copado__Promotion__r.copado__Destination_Environment__c;
            jobTemplateRequest.templateName = templateName;
            jobTemplateRequest.runAfterInstantiation = true;
            return new List<copado.AutomationConnector> {this};
        }
    }

    global override String executeAutomation() {
        return copado.CreateExecution.execute(new List<copado.CreateExecution.Request>{ this.jobTemplateRequest })[0].Id;
    }
   
    global override String getAutomatedActionName() {
        return 'Submit Deployment Status to Jira';
    }
}