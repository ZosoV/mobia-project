#!/bin/bash

curl 'https://mobiala-my.sharepoint.com/personal/mobia_dev_mobia_la/_layouts/15/download.aspx?SourceUrl=%2Fpersonal%2Fmobia%5Fdev%5Fmobia%5Fla%2FDocuments%2Fbase%5Fmodels%2Ezip' \
	-H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0' \
	-H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8' \
	-H 'Accept-Language: en-US,en;q=0.5' \
	--compressed \
	-H 'Referer: https://mobiala-my.sharepoint.com/personal/mobia_dev_mobia_la/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fmobia_dev_mobia_la%2FDocuments%2Fbase_models.zip&parent=%2Fpersonal%2Fmobia_dev_mobia_la%2FDocuments&ga=1' \
	-H 'Upgrade-Insecure-Requests: 1' \
	-H 'Sec-Fetch-Dest: iframe' \
	-H 'Sec-Fetch-Mode: navigate' \
	-H 'Sec-Fetch-Site: same-origin' \
	-H 'Sec-GPC: 1' \
	-H 'DNT: 1' \
	-H 'Connection: keep-alive' \
	-H 'Cookie: FedAuth=77u/PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz48U1A+VjEyLDBoLmZ8bWVtYmVyc2hpcHx1cm4lM2FzcG8lM2Fhbm9uI2Y5NjkyMmI5MThmYTMwMzk1N2RiOWIyZmM4YjZhMTZhYmU2MzdlNzI5ZTNhMTA2YTA3MzdiYTVmNjNmMjA1ZWEsMCMuZnxtZW1iZXJzaGlwfHVybiUzYXNwbyUzYWFub24jZjk2OTIyYjkxOGZhMzAzOTU3ZGI5YjJmYzhiNmExNmFiZTYzN2U3MjllM2ExMDZhMDczN2JhNWY2M2YyMDVlYSwxMzI5NDE2OTc2MzAwMDAwMDAsMCwxMzI5NDI1NTg2MzY2ODA5NzMsMC4wLjAuMCwyNTgsM2Q0MmZiNTYtODY0NS00MDFiLTk1OTktNGE0NTZhNjQ4YzNkLCwsNjBiYjMyYTAtNjBiMC0xMDAwLWE0ZjEtYmYyOGJiMmYzYThkLDYwYmIzMmEwLTYwYjAtMTAwMC1hNGYxLWJmMjhiYjJmM2E4ZCxDYVJ2WDJ1ZjcwTytrb253UFUwWFZBLDAsMCwwLCwsLDI2NTA0Njc3NDM5OTk5OTk5OTksMCwsLCwsLCwwLCxLaEFmY1loOWpqRUNEV2p0MTNQcGtUM2pqNGkzODRESkk0Q2R4NnhkTVpONVRlVTBPTk5tU3hES0tJZ1JaK3VyQm5rMmtGUmdMbTZTRW5KT2IyTmpKT0JUdzVYVXFoa2t3M3ovQ21mTWpuM2V6a25acUh5UjJWZVNPVUpxc1RWMzJ0ZGlnL3RtVThNMDlOUGhtbWFaM1U4S0dBWXlLRDcvNWt0VTIvWXFnTk00ekpjbnBjcEZFaC9BUnZXbXl2WXUweDNMdXBnWklubi85d3k0WVdkbkdCd01BK0FmVlZpNU1rRjNtR3J6bUJUd1Myai9wdE44WUV3clMxcjBBQ1V1K0dtZVZvalZlNEVOQngycTMvK3NXVGhsbTJPSWdzR3dCcWZMMGpvVTk5dHpPb0QzbUVNekkvVEE1bVkvd1dtdHZTdDR0dnFuaDFGQkxJdGtLMFBtT2c9PTwvU1A+; KillSwitchOverrides_enableKillSwitches=; KillSwitchOverrides_disableKillSwitches=' \
	--output test.zip
