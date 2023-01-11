use serenity::model::gateway::Ready;
use serenity::prelude::{Context, EventHandler};

use tracing::info;

pub struct ReadyHandler;

#[serenity::async_trait]
impl EventHandler for ReadyHandler {
    async fn ready(&self, _: Context, ready: Ready) {
        info!("{} is connected!", ready.user.name);
    }
}