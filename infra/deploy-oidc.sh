#!/usr/bin/env bash
#
# One-time bootstrap: Deploy GitHub OIDC to AWS
#
# Usage:
#   ./deploy-oidc.sh <github-org> <github-repo>
#
# Example:
#   ./deploy-oidc.sh peterkrentel ondemand-iam-agentic-ai
#
set -euo pipefail

GITHUB_ORG="${1:-}"
GITHUB_REPO="${2:-}"
STACK_NAME="aimgentix-github-oidc"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -z "$GITHUB_ORG" || -z "$GITHUB_REPO" ]]; then
    echo "Usage: $0 <github-org> <github-repo>"
    echo "Example: $0 peterkrentel ondemand-iam-agentic-ai"
    exit 1
fi

echo "🚀 Deploying GitHub OIDC stack..."
echo "   Org:  $GITHUB_ORG"
echo "   Repo: $GITHUB_REPO"
echo ""

# Deploy the stack
aws cloudformation deploy \
    --template-file "${SCRIPT_DIR}/github-oidc.cfn.yaml" \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        GitHubOrg="$GITHUB_ORG" \
        GitHubRepo="$GITHUB_REPO" \
    --capabilities CAPABILITY_NAMED_IAM \
    --no-fail-on-empty-changeset

# Get outputs
echo ""
echo "✅ Stack deployed!"
echo ""

ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`RoleArn`].OutputValue' \
    --output text)

echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📋 Add this secret to your GitHub repo:"
echo ""
echo "   Settings → Secrets and variables → Actions → New repository secret"
echo ""
echo "   Name:  AWS_ROLE_ARN"
echo "   Value: $ROLE_ARN"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Then run your agent:"
echo "   gh workflow run s3-lifecycle-agent.yml"
echo ""

