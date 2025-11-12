# Script per sincronizzare i CV JSONs dal server Scaleway
# Esegui: .\sync_cvs.ps1

$serverPath = "root@51.158.245.19:/var/lib/docker/piazzati-data/cvs/"
$localPath = ".\NLP\data\cvs\"
$sshKey = "C:\Users\Merye\.ssh\id_piazzati"

Write-Host "Sincronizzando CV JSONs da Scaleway..." -ForegroundColor Green

# Crea la cartella locale se non exists
if (!(Test-Path $localPath)) {
    New-Item -ItemType Directory -Path $localPath -Force
}

# Sincronizza con rsync via SSH
& scp -r -i $sshKey "${serverPath}*" $localPath

Write-Host "Sincronizzazione completata!" -ForegroundColor Green
Write-Host "File disponibili in: $localPath" -ForegroundColor Yellow