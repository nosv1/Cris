use serenity::model::prelude::Message;
use serenity::prelude::{Context, EventHandler};

use crate::servers::tepcott;

pub struct MessageHandler;

#[serenity::async_trait]
impl EventHandler for MessageHandler {
    async fn message(&self, context: Context, msg: Message) {
        let guild_id: String = msg.guild_id.unwrap().0.to_string();  // store guild id

        if guild_id == tepcott::tepcott::GUILD_ID {           // message sent in tepcott server
            tepcott::event_handlers::message::
                message(context.clone(), msg.clone()).await;  // handle tepcott messages
        }

        // message send examples
        // if msg.content.eq("!ping") {
        //     let _ = msg.reply(&context, "Pong!").await;
        //     let _ = msg.channel_id.say(&context.http, "Pong!").await;
        //     let _ = msg.channel_id.send_message(&context.http, |m| {
        //         m.embed(|e| {
        //             e.title("Pong!");
        //             e.description("Pong!");
        //             e.color(Color::BLITZ_BLUE);
        //             e
        //         });
        //         m
        //     }).await;
        // }
    }
}
