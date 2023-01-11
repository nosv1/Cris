use serenity::model::gateway::Ready;
use serenity::prelude::Context;

pub struct ReadyHandler;

pub async fn ready(_ctx: Context, ready: Ready) {
    println!("{} is connected!", ready.user.name);
}