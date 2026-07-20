[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$CollectorUri,

    [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
    [ValidateNotNull()]
    [object]$Record,

    [string]$BearerToken = $env:SERVICETRACER_COLLECTOR_TOKEN,

    [ValidateRange(1, 10)]
    [int]$MaximumAttempts = 3,

    [ValidateRange(1, 60)]
    [int]$InitialRetryDelaySeconds = 2
)

begin {
    Set-StrictMode -Version Latest
    $ErrorActionPreference = 'Stop'

    if ([string]::IsNullOrWhiteSpace($BearerToken)) {
        throw 'A bearer token is required. Supply -BearerToken or set SERVICETRACER_COLLECTOR_TOKEN.'
    }

    $headers = @{ Authorization = "Bearer $BearerToken" }
}

process {
    $body = $Record | ConvertTo-Json -Depth 32 -Compress
    $attempt = 0

    while ($true) {
        $attempt++
        try {
            Invoke-RestMethod -Method Post -Uri $CollectorUri -Headers $headers -ContentType 'application/json' -Body $body -TimeoutSec 30
            break
        }
        catch {
            if ($attempt -ge $MaximumAttempts) {
                throw
            }

            $delay = $InitialRetryDelaySeconds * [math]::Pow(2, $attempt - 1)
            Start-Sleep -Seconds ([int]$delay)
        }
    }
}
