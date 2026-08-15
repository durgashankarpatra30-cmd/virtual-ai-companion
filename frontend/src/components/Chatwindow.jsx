import Message from "./Message";
import "../style/Chatwindow.css";
import {useEffect ,useRef} from "react";

function ChatWindow({ messages, companion ,isTyping}) {

    const chatEndRef = useRef(null);
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    return (

        <div className="chat-window">

            {messages.length === 0 ? (

                <div className="empty-chat">

                    👋 Start chatting with {companion?.name || "your companion"}!

                </div>

            ) : (

                <>
                    {messages.map((msg, index) => (
                        <Message
                            key={index}
                            index={index}
                            message={msg}
                            companion={companion}
                        />
                    ))}
                    {isTyping && (
                        <div className="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </>

            )}

        </div>

    );

}

export default ChatWindow;