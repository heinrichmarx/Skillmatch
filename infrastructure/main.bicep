// SkillMatch - Azure Infrastructure as Code (Bicep)
// Deploys: Azure SQL, App Service (API), Static Web Apps (x2 portals)

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Azure region')
param location string = resourceGroup().location

@description('SQL admin username')
param sqlAdminUser string = 'skillmatch_admin'

@secure()
@description('SQL admin password')
param sqlAdminPassword string

var prefix = 'skillmatch-${environment}'
var sqlServerName = '${prefix}-sql'
var sqlDbName = 'skillmatch_db'
var apiAppName = '${prefix}-api'
var appPlanName = '${prefix}-plan'
var candidateStaticAppName = '${prefix}-candidate'
var recruiterStaticAppName = '${prefix}-recruiter'

// ── SQL SERVER ────────────────────────────────────────────
resource sqlServer 'Microsoft.Sql/servers@2022-05-01-preview' = {
  name: sqlServerName
  location: location
  properties: {
    administratorLogin: sqlAdminUser
    administratorLoginPassword: sqlAdminPassword
    version: '12.0'
    publicNetworkAccess: 'Enabled'
  }
}

resource sqlFirewallAzure 'Microsoft.Sql/servers/firewallRules@2022-05-01-preview' = {
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

resource sqlDatabase 'Microsoft.Sql/servers/databases@2022-05-01-preview' = {
  parent: sqlServer
  name: sqlDbName
  location: location
  sku: {
    name: 'Basic'       // Upgrade to Standard/Premium for production
    tier: 'Basic'
    capacity: 5
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 2147483648  // 2 GB
  }
}

// ── APP SERVICE PLAN ──────────────────────────────────────
resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: appPlanName
  location: location
  sku: {
    name: 'B1'         // Basic tier — upgrade for production
    tier: 'Basic'
    capacity: 1
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// ── API APP SERVICE ───────────────────────────────────────
resource apiApp 'Microsoft.Web/sites@2022-09-01' = {
  name: apiAppName
  location: location
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appCommandLine: 'gunicorn --bind 0.0.0.0:8000 --timeout 120 app:app'
      appSettings: [
        {
          name: 'DATABASE_URL'
          value: 'mssql+pyodbc://${sqlAdminUser}:${sqlAdminPassword}@${sqlServer.properties.fullyQualifiedDomainName}/${sqlDbName}?driver=ODBC+Driver+17+for+SQL+Server'
        }
        {
          name: 'SECRET_KEY'
          value: uniqueString(resourceGroup().id, 'secret')
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'CORS_ORIGINS'
          value: 'https://${candidateStaticApp.properties.defaultHostname},https://${recruiterStaticApp.properties.defaultHostname}'
        }
      ]
      cors: {
        allowedOrigins: [
          'https://${candidateStaticApp.properties.defaultHostname}'
          'https://${recruiterStaticApp.properties.defaultHostname}'
        ]
      }
    }
  }
  dependsOn: [sqlDatabase]
}

// ── STATIC WEB APPS ───────────────────────────────────────
resource candidateStaticApp 'Microsoft.Web/staticSites@2022-09-01' = {
  name: candidateStaticAppName
  location: location
  sku: {
    name: 'Free'       // Upgrade to Standard for custom domains + auth
    tier: 'Free'
  }
  properties: {
    buildProperties: {
      appLocation: '/candidate-portal'
      outputLocation: ''
    }
  }
}

resource recruiterStaticApp 'Microsoft.Web/staticSites@2022-09-01' = {
  name: recruiterStaticAppName
  location: location
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    buildProperties: {
      appLocation: '/recruiter-portal'
      outputLocation: ''
    }
  }
}

// ── OUTPUTS ───────────────────────────────────────────────
output apiUrl string = 'https://${apiApp.properties.defaultHostName}'
output candidatePortalUrl string = 'https://${candidateStaticApp.properties.defaultHostname}'
output recruiterPortalUrl string = 'https://${recruiterStaticApp.properties.defaultHostname}'
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
