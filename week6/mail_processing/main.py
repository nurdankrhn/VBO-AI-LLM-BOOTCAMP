from graph_compile import app
from langgraph.types import Command
import json

def run_email_processor():
    # Get email input from user
    print("=== Email Processing System ===")
    email_content = input("Enter email content: ").strip()
    if not email_content:
        email_content = "I was charged twice for my subscription! This is urgent!"
        print(f"Using default email: {email_content}")
    
    sender_email = input("Enter sender email (or press Enter for default): ").strip()
    if not sender_email:
        sender_email = "customer@example.com"
    
    email_id = input("Enter email ID (or press Enter for default): ").strip()
    if not email_id:
        email_id = "email_123"

    # Create initial state
    initial_state = {
        "email_content": email_content,
        "sender_email": sender_email,
        "email_id": email_id,
        "messages": []
    }

    # Run with a thread_id for persistence
    config = {"configurable": {"thread_id": f"thread_{email_id}"}}
    
    print("\n--- Processing Email ---")
    result = app.invoke(initial_state, config)
    
    # Check if graph paused for human review
    if '__interrupt__' in result:
        interrupt_data = result['__interrupt__'][0].value
        print(f"\n--- Human Review Required ---")
        print(f"Email ID: {interrupt_data['email_id']}")
        print(f"Intent: {interrupt_data['intent']}")
        print(f"Urgency: {interrupt_data['urgency']}")
        print(f"Original Email: {interrupt_data['original_email']}")
        
        if interrupt_data['draft_response']:
            print(f"\nDraft Response:\n{interrupt_data['draft_response']}")
        else:
            print("\nNo draft generated - requires immediate human attention")
        
        # Get human decision
        print(f"\nAction: {interrupt_data['action']}")
        approved = input("Approve response? (y/n): ").lower().startswith('y')
        
        if approved:
            # Check if user wants to edit
            edit = input("Edit response? (y/n): ").lower().startswith('y')
            edited_response = interrupt_data['draft_response']
            
            if edit:
                print("Enter your edited response (press Enter twice when done):")
                lines = []
                while True:
                    line = input()
                    if line == "" and lines and lines[-1] == "":
                        break
                    lines.append(line)
                edited_response = "\n".join(lines[:-1])  # Remove last empty line
            
            # Resume with approval
            human_response = Command(
                resume={
                    "approved": True,
                    "edited_response": edited_response
                }
            )
        else:
            # Reject - human will handle
            human_response = Command(
                resume={"approved": False}
            )
        
        # Resume execution
        print("\n--- Resuming Processing ---")
        final_result = app.invoke(human_response, config)
        
        if approved:
            print("✅ Email sent successfully!")
        else:
            print("❌ Email rejected - will be handled manually")
    
    else:
        # No interruption - email was processed automatically
        if result.get('draft_response'):
            print(f"✅ Email processed automatically")
            print(f"Response sent: {result['draft_response'][:100]}...")
        else:
            print("❌ Email processing failed")

if __name__ == "__main__":
    run_email_processor()