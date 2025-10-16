#!/bin/zsh
# Utility script to print SQL Server connection info for universal-parquet-exporter

echo "Enter SQL Server port (default: 1433):"
echo "Enter SQL Server database name:"
echo "Enter SQL Server username:"
echo "Enter SQL Server password (input will be hidden):"
echo

conf_file=".confSQLConnection"
# Load existing values if file exists
if [ -f "$conf_file" ]; then
	echo "Found existing $conf_file in the current directory."
	source "$conf_file"
else
	SQLSERVER_HOST=""
	SQLSERVER_PORT=""
	SQLSERVER_DATABASE=""
	SQLSERVER_USER=""
	SQLSERVER_PASSWORD=""
fi

# Prompt for each parameter, using existing value if present
echo "Enter SQL Server host (default: localhost):"
if [ -n "$SQLSERVER_HOST" ]; then
	echo "Current: $SQLSERVER_HOST"
	read -p "Is this correct? (y/n): " correct
	if [ "$correct" = "y" ]; then
		host="$SQLSERVER_HOST"
	else
		read -p "Enter new host: " host
		host=${host:-localhost}
	fi
else
	read host
	host=${host:-localhost}
fi

echo "Enter SQL Server port (default: 1433):"
if [ -n "$SQLSERVER_PORT" ]; then
	echo "Current: $SQLSERVER_PORT"
	read -p "Is this correct? (y/n): " correct
	if [ "$correct" = "y" ]; then
		port="$SQLSERVER_PORT"
	else
		read -p "Enter new port: " port
		port=${port:-1433}
	fi
else
	read port
	port=${port:-1433}
fi

echo "Enter SQL Server database name:"
if [ -n "$SQLSERVER_DATABASE" ]; then
	echo "Current: $SQLSERVER_DATABASE"
	read -p "Is this correct? (y/n): " correct
	if [ "$correct" = "y" ]; then
		database="$SQLSERVER_DATABASE"
	else
		read -p "Enter new database: " database
	fi
else
	read database
fi

echo "Enter SQL Server username:"
if [ -n "$SQLSERVER_USER" ]; then
	echo "Current: $SQLSERVER_USER"
	read -p "Is this correct? (y/n): " correct
	if [ "$correct" = "y" ]; then
		username="$SQLSERVER_USER"
	else
		read -p "Enter new username: " username
	fi
else
	read username
fi

echo "Enter SQL Server password (input will be hidden):"
if [ -n "$SQLSERVER_PASSWORD" ]; then
	echo "Current: (hidden)"
	read -p "Is this correct? (y/n): " correct
	if [ "$correct" = "y" ]; then
		password="$SQLSERVER_PASSWORD"
	else
		stty -echo
		read -p "Enter new password: " password
		stty echo
		echo
	fi
else
	stty -echo
	read password
	stty echo
	echo
fi



# Save connection details to .confSQLConnection
cat > "$conf_file" << EOF
SQLSERVER_HOST=$host
SQLSERVER_PORT=$port
SQLSERVER_DATABASE=$database
SQLSERVER_USER=$username
SQLSERVER_PASSWORD=$password
EOF

echo "\n--- SQL Server Connection Information ---"
echo "Connection string for pyodbc:"
echo "DRIVER={ODBC Driver 17 for SQL Server};SERVER=$host,$port;DATABASE=$database;UID=$username;PWD=$password"
echo "\nEnvironment variable exports (optional):"
echo "export SQLSERVER_HOST=$host"
echo "export SQLSERVER_PORT=$port"
echo "export SQLSERVER_DATABASE=$database"
echo "export SQLSERVER_USER=$username"
echo "export SQLSERVER_PASSWORD=********" # Do not print actual password for security
echo "\nConnection details saved to $conf_file. Copy and use these values in your config/sqlserver_config.py or as environment variables."
