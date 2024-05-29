@isTest
private class JiraCloudDeploymentsConnectorTest {
 
    @isTest
    static void testGetAutomatedActionName(){
        Test.startTest();
            JiraCloudDeploymentsConnector ac = new JiraCloudDeploymentsConnector();
            String actionName = ac.getAutomatedActionName();
        Test.stopTest();

        Assert.areEqual('Submit Deployment Status to Jira', actionName);
    }

    @isTest
    static void testExecuteAutomation(){
        System.runAs(createCopadoUser()) {
            copado__JobTemplate__c jobTemplate = new copado__JobTemplate__c(Name = 'Jira_Deployment_Notification_1', copado__ApiName__c = '', copado__Version__c = 0);
            insert jobTemplate;

            insert new copado__JobStep__c(Name = 'Step 1', copado__JobTemplate__c = jobTemplate.Id, copado__Type__c = 'Manual');
    
            jobTemplate = [SELECT Id,Name,copado__ApiName__c,copado__Version__c FROM copado__JobTemplate__c WHERE Id = :jobTemplate.Id];
            JiraCloudDeploymentsConnector.templateName = jobTemplate.copado__ApiName__c;

            copado__Deployment_Flow__c pipeline = new copado__Deployment_Flow__c(copado__Active__c = true);
            insert pipeline;

            copado__Project__c project = new copado__Project__c(copado__Deployment_Flow__c = pipeline.Id);  
            insert project;

            copado__Environment__c s_env = new copado__Environment__c(Name='Source');
            insert s_env;

            copado__Org__c s_org = new copado__Org__c(Name='Source', copado__Environment__c = s_env.id);
            insert s_org;
            
            copado__Environment__c d_env = new copado__Environment__c(Name='Dest');
            insert d_env;

            copado__Org__c d_org = new copado__Org__c(Name='Dest', copado__Environment__c = d_env.id);
            insert d_org;

            copado__Deployment_Flow_Step__c pc = new copado__Deployment_Flow_Step__c(copado__Deployment_Flow__c = pipeline.Id, copado__Source_Environment__c = s_env.id, copado__Destination_Environment__c = d_env.id);
            insert pc;

            copado__Promotion__c promotion = new copado__Promotion__c(copado__Project__c = project.Id, copado__Source_Environment__c = s_env.id, copado__Destination_Environment__c = d_env.id);
            insert promotion;

            promotion = [SELECT Id,Name,copado__Project__c,copado__Destination_Environment__c FROM copado__Promotion__c WHERE Id = :promotion.Id];

            copado__Deployment__c deployment = new copado__Deployment__c(copado__Promotion__c = promotion.Id);

            copado__JobExecution__c promotionJE = new copado__JobExecution__c(copado__Deployment__c = deployment.Id, copado__DataJson__c = '{"deploymentDryRun" : false}');
            insert promotionJE;

            // Automation event
            copado__Automation_Event__c aEvent = new copado__Automation_Event__c(copado__Job_Execution_Id__c = promotionJE.Id, copado__Action_Name__c = 'Promotion', copado__Action_Result__c = '', copado__Action_Status__c = 'Success');
            insert aEvent;

            copado.AutomationConnectorContext connectorContext = new copado.AutomationConnectorContext();
            connectorContext.automationEvents = new copado__Automation_Event__c[]{aEvent};

            Test.startTest();
                JiraCloudDeploymentsConnector ac = new JiraCloudDeploymentsConnector();
                copado.AutomationConnector[] acs = ac.getConnectors(connectorContext);
                Assert.areEqual(1, acs.size());
                String jeId = ((JiraCloudDeploymentsConnector) acs[0]).executeAutomation();
            Test.stopTest();
        }
    }

    private static User createCopadoUser() {
        // Create a User. Note that the profile will not be guaranteed to be System Administrator
        User runAsUser = new User(
            LastName = 'UserLastName',
            Username = 'username.r904673123@myemail.com',
            Email = 'username.r904673123@myemail.com',
            Alias = 'MyAlias',
            TimeZoneSidKey = 'America/Los_Angeles',
            LocaleSidKey = 'en_US',
            EmailEncodingKey = 'UTF-8',
            ProfileId = UserInfo.getProfileId(),
            LanguageLocaleKey = 'en_US'
        );
        insert runAsUser;

        // Assign user licenses and permissionsets to the newly created user
        System.runAs(runAsUser) {
            copado.GlobalAPI copadoGlobalAPI = new copado.GlobalAPI();
            copado.GlobalAPI.UserLicense userLicense = new copado.GlobalAPI.UserLicense();
            userLicense.isCopadoEnabled = true;
            userLicense.isCCMEnabled = true;
            userLicense.userId = runAsUser.Id;
            copadoGlobalAPI.upsertCopadoLicense(userLicense);

            PermissionSetAssignment copadoPermissionSet = new PermissionSetAssignment();
            copadoPermissionSet.PermissionSetId = [SELECT Id, Name FROM PermissionSet WHERE Name = 'Copado_User' LIMIT 1].Id;
            copadoPermissionSet.AssigneeId = runAsUser.Id;    
            insert copadoPermissionSet;
        }

        return runAsUser;
    }
}