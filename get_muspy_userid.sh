#!/usr/bin/env bash

read -p "Your muspy email: " email
read -p "Your muspy password: " password
output=$(curl -s -X GET -H "Authorization: Basic `printf "$email:$password" | openssl enc -base64`" -H "Cache-Control: no-cache" https://muspy.com/api/1/user | python -c 'exec """\nimport sys, json\ntry:\n    print "\\nYour muspy user ID is...\\n{0}\\n\\nAdd the following to your beets config...\\nfollow:\\n    email: %email\\n    password: %password\\n    userid: {0}".format(json.load(sys.stdin)["userid"])\nexcept Exception:\n    print "\\nUnable to retrieve your muspy user ID"\n"""')
echo "$(sed -e "s/%email/$email/; s/%password/$password/" <<< "$output")"
