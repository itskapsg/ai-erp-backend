#!/bin/bash

# ERP Snapshot Cloning System - The Safety Net
# This script ensures erp_test_db always has fresh data from erp_dev_db
# but can never corrupt the main database

set -e  # Exit on any error

DB_USER="erp_admin"
DB_PASSWORD="db_password_123"
DEV_DB="erp_dev_db"
TEST_DB="erp_test_db"

echo "🔄 ERP Snapshot Cloning System - Starting..."
echo "📊 Source: $DEV_DB → Target: $TEST_DB"

# Set PGPASSWORD to avoid password prompts
export PGPASSWORD="$DB_PASSWORD"

# Check if test database exists
echo "🔍 Checking if $TEST_DB exists..."
if psql -U "$DB_USER" -h localhost -lqt | cut -d \| -f 1 | grep -qw "$TEST_DB"; then
    echo "🗑️  Dropping existing $TEST_DB (Clean Slate)..."
    dropdb -U "$DB_USER" -h localhost "$TEST_DB"
    echo "✅ $TEST_DB dropped successfully"
else
    echo "ℹ️  $TEST_DB does not exist, will create fresh"
fi

# Create fresh test database
echo "🏗️  Creating fresh $TEST_DB..."
createdb -U "$DB_USER" -h localhost "$TEST_DB" -O "$DB_USER"
echo "✅ $TEST_DB created successfully"

# Clone data from dev to test
echo "📋 Cloning ALL data from $DEV_DB to $TEST_DB..."
pg_dump -U "$DB_USER" -h localhost "$DEV_DB" | psql -U "$DB_USER" -h localhost "$TEST_DB"

echo "🎉 Snapshot Cloning Complete!"
echo "🔒 Safety Status: $TEST_DB now contains fresh copy of $DEV_DB"
echo "🛡️  Main database $DEV_DB remains untouched and protected"

# Unset password for security
unset PGPASSWORD