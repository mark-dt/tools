#$config = Get-Content config.json | ConvertFrom-Json
#$api_token = $config.api_token
#$uri = $config.uri

$api_token = ''
$root_url = 'https://ggg43721.sprint.dynatracelabs.com/'

$auth_value = "Api-Token $api_token"

$Headers = @{
    Authorization = $auth_value
}

Function Convert-FromUnixDate ($UnixDate) {
   [timezone]::CurrentTimeZone.ToLocalTime(([datetime]'1/1/1970').AddSeconds($UnixDate))
}

function getUptime([String]$host_name ) {
    $url = $root_url + 'api/v2/metrics/query'
    $payload = @{
        metricSelector = 'com.dynatrace.builtin:host.availability'
        entitySelector = 'type("HOST"),entityName("' + $host_name + '")'
        from = '-24h'
        to = 'now'
        resolution = '10m'
    }
    $out = Invoke-WebRequest -Uri $url -Headers $Headers -Body $payload | Select-Object -Expand Content
    $data_json = ConvertFrom-Json $out
    foreach ($res in $data_json.result) {
        foreach ($d in $res.data) {
            [int32[]]$val_array = $d.values
            $i = $val_array.length - 1
            [bool] $last_seen = $false
            # if the hos is down now check last seen
            while ($val_array[$i] -eq 0) {
                $i = $i - 1 
                $last_seen = $true
            }

            if ($last_seen) {
                $unix_timestamp = $d.timestamps[$i] / 1000
                $last_seen_ts = Convert-FromUnixDate $unix_timestamp
                Write-Host 'Last seen: ' $last_seen_ts -NoNewLine
                echo ''
            }
            for (; $i -gt -1; $i--) {
                if ($val_array[$i] -eq 0) {
                    $unix_timestamp = $d.timestamps[$i] / 1000
                    $nice_timestamp = Convert-FromUnixDate $unix_timestamp
                    $now = Get-Date
                    if ($last_seen) {
                        $now = $last_seen_ts
                    }
                    $delta = New-TimeSpan -Start $nice_timestamp -End $now
                    Write-Host 'Uptime ' $delta.ToString() -NoNewLine
                    exit
                }
            }
        }
    }
}

getUptime $args[0]