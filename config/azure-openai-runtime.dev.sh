#!/usr/bin/env bash
# Non-secret runtime profile verified through an Entra-authenticated Cloud Shell call.
# This file intentionally contains no API key, access token, tenant ID, subscription ID,
# or principal identifier.

export AZURE_OPENAI_BASE_URL='https://anthonyedgar30000-5982-resource.openai.azure.com/openai/v1/'
export AZURE_OPENAI_MODEL_DEPLOYMENT='gpt-5-mini'
export AZURE_OPENAI_TOKEN_SCOPE='https://ai.azure.com/.default'
export AZURE_OPENAI_TIMEOUT_SECONDS='30'
export AZURE_OPENAI_MAX_RETRIES='0'
