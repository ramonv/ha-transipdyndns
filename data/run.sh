#!/usr/bin/with-contenv bashio
USERNAME=$(bashio::config 'username')
DOMAIN=$(bashio::config 'domain')
A_RECORD=$(bashio::config 'a_record')
RECORD_TTL=$(bashio::config 'record_ttl')
echo "$(bashio::config 'private_key')" > secret
LF=$'\\\x0A'; cat secret | sed -e "s/-----BEGIN PRIVATE KEY-----/&${LF}/" -e "s/-----END PRIVATE KEY-----/${LF}&${LF}/" | sed -e "s/[^[:blank:]]\{64\}/&${LF}/g" > secret-temp
x=`cat secret-temp;`
echo "$x" > keyfile.pem
rm secret
rm secret-temp
echo $(date)
echo "TransIP Dynamic DNS Updater Started"
transip_dns --user $USERNAME --private_key_file keyfile.pem --domainname $DOMAIN --record_ttl $RECORD_TTL --record_name $A_RECORD --query_ipv4
