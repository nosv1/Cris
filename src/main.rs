pub mod event_handlers;
pub mod servers;

use dotenv::dotenv;

use serenity::Client;
use serenity::framework::StandardFramework;
use serenity::prelude::GatewayIntents;

use tracing::info;

use event_handlers::event_handlers::Handler;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    info!("Connecting bot...");
    dotenv().ok();
    let token = std::env::var("DISCORD_TOKEN").expect("Expected a token in the environment");
    let intents = GatewayIntents::non_privileged() | GatewayIntents::privileged();
    let mut client = Client::builder(token, intents)
        .event_handler(Handler)
        .framework(StandardFramework::new())
        .await?;

    // start listening for events by starting a single shard
    if let Err(why) = client.start().await {
        println!("An error occurred while running the client: {:?}", why);
    }

    Ok(())
}
