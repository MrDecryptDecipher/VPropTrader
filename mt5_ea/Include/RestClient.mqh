//+------------------------------------------------------------------+
//|                                                   RestClient.mqh |
//|                        REST API Client for Sidecar Communication |
//+------------------------------------------------------------------+
#property copyright "Quant Ω Supra AI"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| REST Client Class                                                |
//+------------------------------------------------------------------+
class CRestClient
{
private:
    string m_baseUrl;
    int    m_timeout;
    int    m_retryCount;
    int    m_retryDelay;
    char   m_data[];
    char   m_result[];
    string m_headers;
    
public:
    //--- Constructor
    CRestClient(string baseUrl, int timeout = 5000)
    {
        m_baseUrl = baseUrl;
        m_timeout = timeout;
        m_retryCount = 3;
        m_retryDelay = 1000;
        m_headers = "Content-Type: application/json\r\n";
    }
    
    //--- Get signals from Sidecar
    bool GetSignals(string &response)
    {
        string url = m_baseUrl + "/api/signals";
        return SendRequest("GET", url, "", response);
    }
    
    //--- Post execution report to Sidecar
    bool PostExecution(string jsonData, string &response)
    {
        string url = m_baseUrl + "/api/executions";
        return SendRequest("POST", url, jsonData, response);
    }
    
    //--- Post close report to Sidecar
    bool PostClose(string jsonData, string &response)
    {
        string url = m_baseUrl + "/api/executions/close";
        return SendRequest("POST", url, jsonData, response);
    }
    
    //--- Test connection
    bool TestConnection()
    {
        string response;
        string url = m_baseUrl + "/health";
        return SendRequest("GET", url, "", response);
    }
    
    //--- Generic GET request
    bool Get(string endpoint, string &response)
    {
        string url = m_baseUrl + endpoint;
        return SendRequest("GET", url, "", response);
    }
    
    //--- Generic POST request
    bool Post(string endpoint, string jsonData, string &response)
    {
        string url = m_baseUrl + endpoint;
        return SendRequest("POST", url, jsonData, response);
    }
    
private:
    //--- Send HTTP request with retry logic
    bool SendRequest(string method, string url, string data, string &response)
    {
        ResetLastError();
        
        for(int attempt = 0; attempt < m_retryCount; attempt++)
        {
            // Prepare data
            if(data != "")
            {
                StringToCharArray(data, m_data, 0, StringLen(data));
            }
            
            // Send request
            int res = WebRequest(
                method,
                url,
                m_headers,
                m_timeout,
                m_data,
                m_result,
                m_headers
            );
            
            // Check result
            if(res == 200)
            {
                response = CharArrayToString(m_result);
                return true;
            }
            else if(res == -1)
            {
                int error = GetLastError();
                Print("WebRequest error: ", error, " - ", ErrorDescription(error));
                Print("Make sure URL is added to allowed list in Tools->Options->Expert Advisors");
                
                if(attempt < m_retryCount - 1)
                {
                    Sleep(m_retryDelay * (attempt + 1));
                }
            }
            else
            {
                Print("HTTP error: ", res);
                response = CharArrayToString(m_result);
                
                if(attempt < m_retryCount - 1)
                {
                    Sleep(m_retryDelay);
                }
            }
        }
        
        return false;
    }
    
    //--- Get error description
    string ErrorDescription(int error_code)
    {
        switch(error_code)
        {
            case 4060: return "Function not allowed";
            case 5203: return "Object does not exist";
            case 4014: return "System is busy";
            default: return "Error " + IntegerToString(error_code);
        }
    }
};

//+------------------------------------------------------------------+
