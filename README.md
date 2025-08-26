<p align="center"><a href="https://www.growthbook.io"><img src="https://cdn.growthbook.io/growthbook-logo@2x.png" width="400px" alt="GrowthBook - Open Source Feature Flagging and A/B Testing" /></a></p>
<p align="center"><b>Open Source Feature Flagging and A/B Testing</b></p>
<p align="center">
    <a href="https://github.com/growthbook/growthbook/github/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/growthbook/growthbook/ci.yml?branch=main" alt="Build Status" height="22"/></a>
    <a href="https://github.com/growthbook/growthbook/releases"><img src="https://img.shields.io/github/v/release/growthbook/growthbook?color=blue&sort=semver" alt="Release" height="22"/></a>
    <a href="https://slack.growthbook.io?ref=readme-badge"><img src="https://img.shields.io/badge/slack-join-E01E5A?logo=slack" alt="Join us on Slack" height="22"/></a>
</p>

Get up and running in 1 minute with:

```sh
git clone https://github.com/growthbook/growthbook.git
cd growthbook
docker compose up -d
```

Then visit http://localhost:3000

[![GrowthBook Screenshot](/features-screenshot.png)](https://www.growthbook.io)

## Our Philosophy

The top 1% of companies spend thousands of hours building their own feature flagging and A/B testing platforms in-house.
The other 99% are left paying for expensive 3rd party SaaS tools or hacking together unmaintained open source libraries.

We want to give all companies the flexibility and power of a fully-featured in-house platform without needing to build it themselves.

## Major Features

- 🏁 Feature flags with advanced targeting, gradual rollouts, and experiments
- 💻 SDKs for [React](https://docs.growthbook.io/lib/react), [Javascript](https://docs.growthbook.io/lib/js), [PHP](https://docs.growthbook.io/lib/php), [Ruby](https://docs.growthbook.io/lib/ruby), [Python](https://docs.growthbook.io/lib/python), [Go](https://docs.growthbook.io/lib/go), [Android](https://docs.growthbook.io/lib/kotlin), [iOS](https://docs.growthbook.io/lib/swift), and [more](https://docs.growthbook.io/lib)!
- 🆎 Powerful A/B test analysis with advanced statistics (CUPED, Sequential testing, Bayesian, SRM checks, and more)
- ❄️ Use your existing data stack - BigQuery, Mixpanel, Redshift, Google Analytics, [and more](https://docs.growthbook.io/app/datasources)
- ⬇️ Drill down into A/B test results by browser, country, or any other custom attribute
- 🪐 Export reports as a Jupyter Notebook!
- 📝 Document everything with screenshots and GitHub Flavored Markdown throughout
- 🔔 Webhooks and a REST API for building integrations

## Try GrowthBook

### Managed Cloud Hosting

Create a free [GrowthBook Cloud](https://app.growthbook.io) account to get started.

### Open Source

The included [docker-compose.yml](https://github.com/growthbook/growthbook/blob/main/docker-compose.yml) file contains the GrowthBook App and a MongoDB instance (for storing cached experiment results and metadata):

```sh
git clone https://github.com/growthbook/growthbook.git
cd growthbook
docker compose up -d
```

Then visit http://localhost:3000 to view the app.

Check out the full [Self-Hosting Instructions](https://docs.growthbook.io/self-host) for more details.

## Documentation and Support

View the [GrowthBook Docs](https://docs.growthbook.io) for info on how to configure and use the platform.

Join [our Slack community](https://slack.growthbook.io?ref=readme-support) if you get stuck, want to chat, or are thinking of a new feature.

Or email us at [hello@growthbook.io](mailto:hello@growthbook.io) if Slack isn't your thing.

We're here to help - and to make GrowthBook even better!

## Contributors

We ❤️ all contributions, big and small!

Read [CONTRIBUTING.md](/CONTRIBUTING.md) for how to setup your local development environment.

If you want to, you can reach out via [Slack](https://slack.growthbook.io?ref=readme-contributing) or [email](mailto:hello@growthbook.io) and we'll set up a pair programming session to get you started.

## License

GrowthBook is an Open Core product. The bulk of the code is under the permissive MIT license. There are several directories that are governed under a separate commercial license, the GrowthBook Enterprise License.

View the `LICENSE` file in this repository for the full text and details.

![GrowthBook Repository Stats](https://repobeats.axiom.co/api/embed/13ffc63ec5ce7fe45efa95dd326d9185517f0a15.svg "GrowthBook Repository Stats")

# GrowthBook - A/B Testing & Feature Flag Platform

GrowthBook is an open-source platform for A/B testing and feature flags. It provides a complete solution for running experiments, managing feature flags, and analyzing results.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
  - [Datasources](#datasources)
  - [Fact Tables](#fact-tables)
  - [Metrics](#metrics)
  - [Features](#features)
  - [Experiments](#experiments)
- [Integrations](#integrations)
  - [Python Integration](#python-integration)
  - [Next.js Integration](#nextjs-integration)
- [Advanced Features](#advanced-features)
- [API Reference](#api-reference)

## Overview

GrowthBook helps you:
- **Run A/B Tests**: Test different variations of your product
- **Feature Flags**: Safely roll out new features
- **Real-time Analytics**: Get instant results and insights
- **Targeting**: Target specific users or segments
- **Integration**: Works with any tech stack

## Quick Start

### 1. Start GrowthBook

```bash
# Start all services
docker-compose -f docker-compose.docdb.yml up -d

# Check status
docker-compose -f docker-compose.docdb.yml ps
```

### 2. Access the Platform

- **Frontend**: http://10.0.31.135
- **API**: http://10.0.31.135/api
- **Exposure API**: http://10.0.31.135/exposure

## Core Concepts

### Datasources

Datasources connect GrowthBook to your data warehouse (Redshift, BigQuery, Snowflake, etc.).

#### Setting up a Datasource

1. **Go to Settings → Datasources**
2. **Click "Add Datasource"**
3. **Select your database type** (Redshift, BigQuery, etc.)
4. **Configure connection**:
   ```json
   {
     "host": "your-warehouse.redshift.amazonaws.com",
     "port": 5439,
     "database": "analytics",
     "user": "growthbook_user",
     "password": "your_password"
   }
   ```

#### Supported Datasources

- **Redshift** (AWS)
- **BigQuery** (Google Cloud)
- **Snowflake**
- **PostgreSQL**
- **MySQL**
- **ClickHouse**

### Fact Tables

Fact tables define the events and metrics you want to track in your experiments.

#### Creating a Fact Table

1. **Go to Fact Tables**
2. **Click "Create Fact Table"**
3. **Define the table structure**:

```sql
-- Example: User signup events
SELECT 
  user_id,
  timestamp,
  'signup' as event_name,
  country,
  source
FROM user_events 
WHERE event_type = 'signup'
```

#### Fact Table Configuration

- **Name**: Descriptive name (e.g., "User Signups")
- **Description**: What this table tracks
- **SQL Query**: The query that defines your events
- **User ID Column**: Which column identifies users
- **Timestamp Column**: When events occurred
- **Filters**: Optional conditions to include/exclude data

### Metrics

Metrics measure the success of your experiments.

#### Types of Metrics

1. **Count Metrics**: Number of events (e.g., signups, purchases)
2. **Ratio Metrics**: Conversion rates (e.g., signup rate)
3. **Duration Metrics**: Time-based metrics (e.g., session duration)
4. **Revenue Metrics**: Monetary values (e.g., revenue per user)

#### Creating a Metric

1. **Go to Metrics**
2. **Click "Create Metric"**
3. **Configure the metric**:

```sql
-- Example: Signup Rate
SELECT 
  COUNT(DISTINCT user_id) as numerator,
  COUNT(DISTINCT visitor_id) as denominator
FROM user_events 
WHERE event_type = 'signup'
```

#### Metric Settings

- **Type**: Count, Ratio, Duration, Revenue
- **SQL**: Query to calculate the metric
- **Tags**: Organize metrics (e.g., "conversion", "engagement")
- **Owner**: Who manages this metric

### Features

Features are flags that control functionality in your application.

#### Creating a Feature

1. **Go to Features**
2. **Click "Create Feature"**
3. **Configure the feature**:

```json
{
  "id": "new_checkout_flow",
  "name": "New Checkout Flow",
  "description": "Updated checkout experience",
  "defaultValue": false,
  "valueType": "boolean"
}
```

#### Feature Types

- **Boolean**: On/off flags
- **String**: Text values
- **Number**: Numeric values
- **JSON**: Complex objects

#### Targeting Rules

```json
{
  "rules": [
    {
      "type": "force",
      "condition": {
        "country": "US"
      },
      "value": true
    },
    {
      "type": "rollout",
      "condition": {
        "userType": "premium"
      },
      "value": true,
      "coverage": 0.5
    }
  ]
}
```

### Experiments

Experiments test different variations to see which performs better.

#### Creating an Experiment

1. **Go to Experiments**
2. **Click "Create Experiment"**
3. **Configure the experiment**:

```json
{
  "name": "Checkout Button Color Test",
  "hypothesis": "Red buttons will increase conversions",
  "variations": [
    {
      "name": "Control",
      "value": "blue"
    },
    {
      "name": "Treatment",
      "value": "red"
    }
  ],
  "metrics": ["signup_rate", "revenue_per_user"],
  "targeting": {
    "country": ["US", "CA"],
    "userType": "new"
  }
}
```

#### Experiment Settings

- **Name**: Descriptive experiment name
- **Hypothesis**: What you're testing
- **Variations**: Different versions to test
- **Metrics**: Success criteria
- **Targeting**: Who sees the experiment
- **Sample Size**: How many users to include

#### Running Experiments

1. **Draft**: Set up the experiment
2. **Running**: Active and collecting data
3. **Stopped**: No longer running
4. **Archived**: Historical record

#### Analyzing Results

GrowthBook provides:
- **Statistical Significance**: p-values and confidence intervals
- **Lift**: Percentage improvement
- **Sample Size**: How many users in each variation
- **Segments**: Breakdown by user characteristics

## Integrations

### Python Integration

#### Installation

```bash
pip install growthbook
```

#### Basic Setup

```python
from growthbook import GrowthBook
import requests

# Initialize GrowthBook
gb = GrowthBook(
    api_host="http://10.0.31.135",
    client_key="sdk-ATi82gwSt8HCUwx8",
    attributes={
        "id": "user123",
        "country": "US",
        "userType": "premium"
    }
)

# Load features
gb.load_features()
```

#### Complete Integration Example

```python
"""
GrowthBook integration helper for A/B testing and feature flags.
"""
import requests
from typing import Optional, Dict, Any, Callable
from growthbook import GrowthBook

from helper.utils import (
    get_ds_user_id, 
    get_ds_session_id, 
    get_user_agent, 
    get_user_country, 
    get_user_city, 
    get_user_currency, 
    get_user_locale, 
    get_utm_params, 
    get_ip_address,
    get_kf_verified_status
)
from library.logging_lib import get_logger
from settings import config
from common_assets.base.utils import fetch_platform_type

logger = get_logger(__name__)

# Global GrowthBook instance
_growthbook = None


def get_growthbook_attributes() -> Dict[str, Any]:
    """Get all user attributes for GrowthBook using header-based naming."""
    attributes = {
        "id": get_ds_user_id(), 
        "ds_user_id": get_ds_user_id(),
        "ds_session_id": get_ds_session_id(),
        "user_agent": get_user_agent(),
        "geo_country_code": get_user_country(),
        "geo_city": get_user_city(),
        "currency_id": get_user_currency(),
        "locale": get_user_locale(),
        "utm": get_utm_params(),
        "forwarded_for": get_ip_address(),
        "is_kf_verified": get_kf_verified_status(),
        "platform": fetch_platform_type()
    }
    
    # Remove None values to keep attributes clean
    return {k: v for k, v in attributes.items() if v is not None and v != ""}


def initialize_growthbook(
    api_host: str,
    client_key: str,
    cache_ttl: int = 300,
    on_experiment_viewed: Optional[Callable] = None
) -> GrowthBook:
    """Initialize the global GrowthBook instance."""
    global _growthbook
    
    try:
        # Get user attributes using the centralized method
        attributes = get_growthbook_attributes()
        
        logger.info(f"[GROWTHBOOK] Initializing with attributes: {attributes}")
        
        _growthbook = GrowthBook(
            api_host=api_host,
            client_key=client_key,
            attributes=attributes,
            on_experiment_viewed=on_experiment_viewed,
            cache_ttl=cache_ttl
        )
        try:
            _growthbook.load_features()
            logger.info(f"[GROWTHBOOK] Initialized with API host: {api_host}")
            return _growthbook
        except Exception as e:
            logger.error(f"[GROWTHBOOK] Failed to load features from {api_host}: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"[GROWTHBOOK] Failed to initialize: {str(e)}")
        return None


def is_growthbook_available() -> bool:
    """Check if GrowthBook is available and configured."""
    return _growthbook is not None


def get_feature_enable_status_growthbook(feature_name: str) -> bool:
    """Get feature enable status from GrowthBook."""
    if not is_growthbook_available():
        return False
    try:
        return _growthbook.is_on(feature_name)
    except Exception as e:
        logger.error(f"[GROWTHBOOK] Error checking feature '{feature_name}': {str(e)}")
        return False


def get_experiment_variant_growthbook(feature_name: str) -> Optional[str]:
    """Get experiment variant from GrowthBook."""
    if not is_growthbook_available():
        return None
    try:
        logger.info(f"[GROWTHBOOK] Getting feature value for: {feature_name}")
        logger.info(f"[GROWTHBOOK] Current user attributes: {_growthbook.get_attributes()}")
        
        # Check if feature is enabled first
        is_enabled = _growthbook.is_on(feature_name)
        logger.info(f"[GROWTHBOOK] Feature {feature_name} is_on: {is_enabled}")
        
        # Get the feature value
        value = _growthbook.get_feature_value(feature_name, None)
        logger.info(f"[GROWTHBOOK] Feature {feature_name} value: {value}")
        
        return value
    except Exception as e:
        logger.error(f"[GROWTHBOOK] Error getting variant for '{feature_name}': {str(e)}")
        return None


def on_experiment_viewed(experiment, result):
    """Callback function when an experiment is viewed."""
    try:
        logger.info(f"[GROWTHBOOK] Experiment viewed: {experiment.key} - Variation: {result.variationId}")
        api_base_url = config.EXPOSURE_API_BASE_URL
        logger.info(f"[GROWTHBOOK] Using exposure API URL: {api_base_url}")
        
        # Prepare exposure data using the centralized attributes method
        exposure_data = {
            "ds_user_id": get_ds_user_id(),
            "experiment_id": experiment.key,
            "variation_id": result.key,
            "attributes": get_growthbook_attributes(),
            "source": "search_core_python"
        }
        
        # Log to API server
        response = requests.post(
            f"{api_base_url}",
            json=exposure_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            logger.info(f"[GROWTHBOOK] ✅ Exposure logged for {experiment.key}")
        else:
            logger.error(f"[GROWTHBOOK] ❌ Failed to log exposure: {response.status_code}")
            logger.error(f"[GROWTHBOOK] Response body: {response.text}")

    except Exception as e:
        logger.error(f"[GROWTHBOOK] Error in experiment exposure callback: {str(e)}")


# Usage Examples
def example_feature_flag():
    """Example: Using feature flags"""
    if get_feature_enable_status_growthbook("new_checkout_flow"):
        # Show new checkout
        return "new_checkout"
    else:
        # Show old checkout
        return "old_checkout"


def example_experiment():
    """Example: Using experiments"""
    variant = get_experiment_variant_growthbook("button_color_test")
    
    if variant == "red":
        return "red_button"
    elif variant == "blue":
        return "blue_button"
    else:
        return "default_button"


def example_initialization():
    """Example: Full initialization"""
    # Initialize GrowthBook
    gb = initialize_growthbook(
        api_host="http://10.0.31.135",
        client_key="sdk-ATi82gwSt8HCUwx8",
        on_experiment_viewed=on_experiment_viewed
    )
    
    if gb:
        # Use features and experiments
        if get_feature_enable_status_growthbook("new_feature"):
            print("New feature is enabled!")
        
        variant = get_experiment_variant_growthbook("my_experiment")
        print(f"Experiment variant: {variant}")
```

#### Usage Patterns

```python
# 1. Feature Flags
if get_feature_enable_status_growthbook("new_ui"):
    show_new_interface()
else:
    show_old_interface()

# 2. A/B Testing
variant = get_experiment_variant_growthbook("pricing_test")
if variant == "premium":
    show_premium_pricing()
elif variant == "basic":
    show_basic_pricing()

# 3. Gradual Rollouts
if get_feature_enable_status_growthbook("beta_feature"):
    enable_beta_features()
```

### Next.js Integration

#### Installation

```bash
npm install @growthbook/growthbook
# or
yarn add @growthbook/growthbook
```

#### Setup

```typescript
// lib/growthbook.ts
import { GrowthBook } from '@growthbook/growthbook';

let gb: GrowthBook;

export function initGrowthBook() {
  gb = new GrowthBook({
    apiHost: 'http://10.0.31.135',
    clientKey: 'sdk-ATi82gwSt8HCUwx8',
    enableDevMode: process.env.NODE_ENV === 'development',
    onExperimentView: (experiment, result) => {
      // Log exposure
      fetch('/exposure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ds_user_id: getUserId(),
          experiment_id: experiment.key,
          variation_id: result.key,
          attributes: getAttributes(),
          source: 'nextjs'
        })
      });
    }
  });
  
  return gb;
}

export function getGrowthBook() {
  return gb;
}
```

#### React Hook

```typescript
// hooks/useGrowthBook.ts
import { useEffect, useState } from 'react';
import { GrowthBook } from '@growthbook/growthbook';

export function useGrowthBook() {
  const [gb, setGb] = useState<GrowthBook | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const init = async () => {
      const growthbook = new GrowthBook({
        apiHost: 'http://10.0.31.135',
        clientKey: 'sdk-ATi82gwSt8HCUwx8',
        attributes: {
          id: getUserId(),
          country: getUserCountry(),
          userType: getUserType()
        }
      });

      await growthbook.loadFeatures();
      setGb(growthbook);
      setLoading(false);
    };

    init();
  }, []);

  return { gb, loading };
}
```

#### Component Usage

```tsx
// components/FeatureFlag.tsx
import { useGrowthBook } from '../hooks/useGrowthBook';

interface FeatureFlagProps {
  feature: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function FeatureFlag({ feature, children, fallback }: FeatureFlagProps) {
  const { gb, loading } = useGrowthBook();

  if (loading) return <div>Loading...</div>;
  
  if (gb?.isOn(feature)) {
    return <>{children}</>;
  }
  
  return <>{fallback}</>;
}

// components/Experiment.tsx
import { useGrowthBook } from '../hooks/useGrowthBook';

interface ExperimentProps {
  experiment: string;
  variations: {
    [key: string]: React.ReactNode;
  };
  fallback?: React.ReactNode;
}

export function Experiment({ experiment, variations, fallback }: ExperimentProps) {
  const { gb, loading } = useGrowthBook();

  if (loading) return <div>Loading...</div>;
  
  const value = gb?.getFeatureValue(experiment);
  
  if (value && variations[value]) {
    return <>{variations[value]}</>;
  }
  
  return <>{fallback}</>;
}
```

#### Page Usage

```tsx
// pages/index.tsx
import { FeatureFlag } from '../components/FeatureFlag';
import { Experiment } from '../components/Experiment';

export default function HomePage() {
  return (
    <div>
      <h1>Welcome to Our App</h1>
      
      {/* Feature Flag Example */}
      <FeatureFlag feature="new_header" fallback={<OldHeader />}>
        <NewHeader />
      </FeatureFlag>
      
      {/* Experiment Example */}
      <Experiment 
        experiment="button_color_test"
        variations={{
          red: <button className="bg-red-500">Click Me</button>,
          blue: <button className="bg-blue-500">Click Me</button>
        }}
        fallback={<button className="bg-gray-500">Click Me</button>}
      />
      
      {/* Conditional Content */}
      <FeatureFlag feature="premium_features">
        <PremiumFeatures />
      </FeatureFlag>
    </div>
  );
}
```

#### API Routes

```typescript
// pages/api/exposure.ts
import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const { ds_user_id, experiment_id, variation_id, attributes, source } = req.body;

    // Forward to GrowthBook exposure API
    const response = await fetch('http://10.0.31.135/exposure', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ds_user_id,
        experiment_id,
        variation_id,
        attributes,
        source: 'nextjs'
      })
    });

    if (response.ok) {
      res.status(200).json({ success: true });
    } else {
      res.status(500).json({ error: 'Failed to log exposure' });
    }
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
}
```

## Advanced Features

### On-the-Fly Changes

You can modify feature values and experiment configurations without redeploying:

1. **Go to Features** or **Experiments**
2. **Edit the configuration**
3. **Save changes**
4. **Changes take effect immediately**

### Role-Based Access

```json
{
  "roles": {
    "admin": {
      "permissions": ["*"]
    },
    "analyst": {
      "permissions": ["read:experiments", "read:metrics"]
    },
    "developer": {
      "permissions": ["read:features", "write:features"]
    }
  }
}
```

### Targeting Rules

```json
{
  "rules": [
    {
      "type": "force",
      "condition": {
        "userType": "premium",
        "country": "US"
      },
      "value": true
    },
    {
      "type": "rollout",
      "condition": {
        "userType": "new"
      },
      "value": true,
      "coverage": 0.25
    }
  ]
}
```

### Gradual Rollouts

1. **Start with 0%** coverage
2. **Gradually increase** to 100%
3. **Monitor metrics** for issues
4. **Roll back** if problems occur

## API Reference

### Exposure API

```bash
# Log experiment exposure
POST /exposure
{
  "ds_user_id": "user123",
  "experiment_id": "button_test",
  "variation_id": "red",
  "attributes": {
    "country": "US",
    "userType": "premium"
  },
  "source": "web"
}

# Get user exposures
GET /exposures/{user_id}

# Get experiment exposures
GET /exposures/experiment/{experiment_key}

# Health check
GET /health
```

### Features API

```bash
# Get features for SDK
GET /api/features/{client_key}

# Create feature
POST /api/features
{
  "id": "new_feature",
  "name": "New Feature",
  "defaultValue": false
}
```

### Experiments API

```bash
# Get experiments
GET /api/experiments

# Create experiment
POST /api/experiments
{
  "name": "Button Test",
  "hypothesis": "Red buttons increase clicks",
  "variations": [
    {"name": "Control", "value": "blue"},
    {"name": "Treatment", "value": "red"}
  ]
}
```

## Best Practices

### 1. Experiment Design

- **Clear Hypothesis**: What are you testing?
- **Single Variable**: Test one change at a time
- **Statistical Power**: Ensure adequate sample size
- **Duration**: Run for at least 1-2 weeks

### 2. Feature Flags

- **Descriptive Names**: Use clear, meaningful names
- **Documentation**: Document what each flag does
- **Cleanup**: Remove unused flags
- **Monitoring**: Watch for performance impact

### 3. Metrics

- **Primary Metric**: One main success metric
- **Secondary Metrics**: Additional insights
- **Guardrail Metrics**: Watch for negative effects
- **Segmentation**: Break down by user types

### 4. Targeting

- **Gradual Rollouts**: Start small, scale up
- **User Segmentation**: Target specific groups
- **Geographic Testing**: Test in specific regions
- **Time-based**: Schedule feature releases

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check API keys and authentication
2. **Missing Data**: Verify datasource connections
3. **No Results**: Check experiment targeting and sample size
4. **Slow Loading**: Optimize queries and caching

### Debug Mode

Enable debug logging:

```python
# Python
import logging
logging.getLogger('growthbook').setLevel(logging.DEBUG)
```

```typescript
// Next.js
const gb = new GrowthBook({
  enableDevMode: true,
  // ... other options
});
```

## Support

- **Documentation**: [docs.growthbook.io](https://docs.growthbook.io)
- **GitHub**: [github.com/growthbook/growthbook](https://github.com/growthbook/growthbook)
- **Discord**: [discord.gg/growthbook](https://discord.gg/growthbook)

---

**Note**: This documentation is for GrowthBook version running on your local instance. For the latest features and updates, refer to the official GrowthBook documentation.
