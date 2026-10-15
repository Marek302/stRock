const username = process.env.MONGO_USER;
const password = process.env.MONGO_PASSWORD;
const dbName = process.env.MONGO_DB_NAME;

const db = db.getSiblingDB(dbName)

try{
    db.createUser({
    user: username,
    pwd: password,
    roles: [
        { role: "readWrite", db: dbName }
    ]
    });
    print(`User ${username} created successfully.`)

    db.createCollection('initialization_log');
    db.initialization_log.insertOne({ 
        status: "ready", 
        timestamp: new Date() 
    });
    print(`Database ${dbName} is now active.`);
}catch (err)
{
    print("FATAL ERROR: " + err.message)
    quit(1)
}




