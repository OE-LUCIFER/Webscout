from webscout.webai import Main

def use_rawdog_with_webai(prompt):
    """
    Wrap the webscout default method in a try-except block to catch any unhandled
    exceptions and print a helpful message.
    """
    try:
        webai_bot = Main(
            max_tokens=500, 
            provider="reka",
            temperature=0.7,  
            top_k=40,          
            top_p=0.95,        
            model="reka-core",  # Replace with your desired model
            auth="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjlkbnNsSDdfZlJNNWRXNkFlc1piSiJ9.eyJpc3MiOiJodHRwczovL2F1dGgucmVrYS5haS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDExNDMxMzYxMTUyMDY1OTgxNTAxOSIsImF1ZCI6WyJodHRwczovL2FwaS5yZWthLmFpIiwiaHR0cHM6Ly9wcm9kdWN0aW9uLXJla2EtYWkuZXUuYXV0aDAuY29tL3VzZXJpbmZvIl0sImlhdCI6MTcxNDA1Mzc0NCwiZXhwIjoxNzE0MTQwMTQ0LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIG9mZmxpbmVfYWNjZXNzIiwiYXpwIjoiYmFxNFExOG9Tc0JpV053RGFOQzRtNWhmZ1FHd1V1cE0ifQ.WwExsvIaCc9hxif6l9syUtdjUQI7CUGttXihxIqaDDRQunTF_nK3Ng4QhsGImQKcdZZ608PAGnjdaLeB-5qsocqgovR4Kr9UxuLB4rQ0JtbsrPcCJi3gqFCtfx23-HO8RdrTzmXqd1PVhQTIIX6e65Mg84bgqG_KvHTnRe34yqUIcRsL2DIApk3yl7FrQHOLMaIJ-qjrvcLRVPcpCPUHj_uP5rh63haikt9dRKogSPQiuHPkoHOjGBU1LpYuAMSJZZC2lAM7OV7gFqgB5xvDn9zFSSuUSq0MYhvzl7Vlpg9MZ1dcL79w5m1OitWClXXpt9oqE2TiJgx6eGkUUx_aqw",     # Replace with your auth key/value (if needed)
            timeout=30,
            disable_conversation=True,
            filepath=None,
            update_file=True,
            intro=None,
            rawdog=True,
            history_offset=10250,
            awesome_prompt=None,
            proxy_path=None,
            quiet=True
        )
        webai_response = webai_bot.default(prompt) 
    except Exception as e:
        print("Unexpected error:", e)


if __name__ == "__main__":
    user_prompt = input("Enter your prompt: ")
    use_rawdog_with_webai(user_prompt)
