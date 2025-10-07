#!/usr/bin/env node

/**
 * Seed script for populating the jobs table with sample data
 * 
 * This script reads sample job data from sample_jobs.json and inserts it into
 * the jobs table using Supabase client.
 * 
 * Prerequisites:
 * 1. Create a Supabase project at https://supabase.com
 * 2. Run the migration file: migrations/001_initial.sql
 * 3. Set up environment variables (see instructions below)
 * 4. Install dependencies: npm install @supabase/supabase-js
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// Load environment variables
require('dotenv').config();

// Supabase configuration
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Missing Supabase credentials!');
  console.error('Please set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file');
  console.error('See setup instructions below.');
  process.exit(1);
}

// Create Supabase client
const supabase = createClient(supabaseUrl, supabaseKey);

/**
 * Load sample jobs from JSON file
 */
function loadSampleJobs() {
  try {
    const filePath = path.join(__dirname, 'sample_jobs.json');
    const fileContent = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(fileContent);
  } catch (error) {
    console.error('❌ Error loading sample_jobs.json:', error.message);
    process.exit(1);
  }
}

/**
 * Insert jobs into the database
 */
async function seedJobs() {
  console.log('🌱 Starting job seeding process...');
  
  const jobs = loadSampleJobs();
  console.log(`📄 Loaded ${jobs.length} sample jobs from sample_jobs.json`);
  
  // Prepare jobs for insertion
  const jobsToInsert = jobs.map(job => ({
    source: job.source,
    title: job.title,
    company: job.company,
    location: job.location,
    posted_at: job.posted_at,
    raw: {
      description: job.description,
      requirements: job.requirements,
      nice_to_have: job.nice_to_have,
      salary_range: job.salary_range,
      employment_type: job.employment_type
    }
  }));
  
  try {
    // Insert jobs into the database
    const { data, error } = await supabase
      .from('jobs')
      .insert(jobsToInsert)
      .select('id, title, company');
    
    if (error) {
      console.error('❌ Error inserting jobs:', error);
      process.exit(1);
    }
    
    console.log('✅ Successfully inserted jobs:');
    data.forEach(job => {
      console.log(`   - ${job.title} at ${job.company} (ID: ${job.id})`);
    });
    
    console.log(`\n🎉 Seeding completed! Inserted ${data.length} jobs into the database.`);
    
  } catch (error) {
    console.error('❌ Unexpected error during seeding:', error);
    process.exit(1);
  }
}

/**
 * Verify database connection and table structure
 */
async function verifyDatabase() {
  console.log('🔍 Verifying database connection...');
  
  try {
    // Test connection by querying the jobs table
    const { data, error } = await supabase
      .from('jobs')
      .select('count')
      .limit(1);
    
    if (error) {
      console.error('❌ Database connection failed:', error.message);
      console.error('Make sure you have:');
      console.error('1. Created a Supabase project');
      console.error('2. Run the migration: migrations/001_initial.sql');
      console.error('3. Set correct environment variables');
      process.exit(1);
    }
    
    console.log('✅ Database connection successful!');
    
  } catch (error) {
    console.error('❌ Database verification failed:', error.message);
    process.exit(1);
  }
}

/**
 * Main execution function
 */
async function main() {
  console.log('🚀 CareerPilot Job Seeding Script');
  console.log('==================================\n');
  
  await verifyDatabase();
  await seedJobs();
  
  console.log('\n📋 Next steps:');
  console.log('1. Verify the data in your Supabase dashboard');
  console.log('2. Test the API endpoints with the seeded data');
  console.log('3. Run the frontend to see jobs in action!');
}

// Run the script
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Script failed:', error);
    process.exit(1);
  });
}

module.exports = { seedJobs, loadSampleJobs };
