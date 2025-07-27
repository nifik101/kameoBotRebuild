```mermaid
graph TD
    subgraph Användargränssnitt / Triggers
        CLI["Command Line\n(cli.py)"]
        API["Web API\n(api.py)"]
        Frontend["Frontend\n(React/Vite)"]
    end

    subgraph Logik / Mellanhand
        CLI_Wrapper["KameoBotCLI Class\n(cli.py)"]
        JobService["JobService\n(job_service.py)"]
    end

    subgraph Kärn-Services
        LoanCollector["LoanCollectorService\n(loan_collector.py)"]
        BiddingService["BiddingService\n(bidding_service.py)"]
        LoanRepository["LoanRepository\n(loan_repository.py)"]
    end
    
    subgraph Extern / Data
        KameoAPI["Kameo.se API"]
        Database["SQLite Databas\n(loans.db)"]
        WebSocket["WebSocket Manager\n(websocket_handler.py)"]
    end

    %% Flöden
    
    %% 1. CLI-flödet (Direkt och korrekt)
    CLI -- "kallar metoder på" --> CLI_Wrapper
    CLI_Wrapper -- "använder" --> LoanCollector
    CLI_Wrapper -- "använder" --> BiddingService
    CLI_Wrapper -- "använder" --> LoanRepository
    
    %% 2. API-flöde via CLI Wrapper (Inkorrekt design, kodduplicering)
    API -- "anropar /api/loans/fetch (synkront)" --> CLI_Wrapper
    
    %% 3. API-flöde via JobService (Asynkront och korrekt för web)
    API -- "anropar /api/jobs/fetch-loans (asynkront)" --> JobService
    JobService -- "startar bakgrundsjobb som använder" --> LoanCollector
    
    %% 4. Frontend & WebSocket-flöde
    Frontend -- "anropar" --> API
    Frontend -- "ansluter till" --> WebSocket
    WebSocket -- "sänder realtidsdata till" --> Frontend
    subgraph All Services
      LoanCollector -- "kan logga till" --> WebSocket
      BiddingService -- "kan logga till" --> WebSocket
      JobService -- "kan logga till" --> WebSocket
    end

    %% Service-interaktioner med externa system
    LoanCollector -- "hämtar data från" --> KameoAPI
    BiddingService -- "interagerar med" --> KameoAPI
    LoanCollector -- "konverterar & skickar data till" --> LoanRepository
    LoanRepository -- "sparar/läser från" --> Database

    %% Styling för att tydliggöra problem
    style CLI_Wrapper fill:#f9f,stroke:#333,stroke-width:2px
    linkStyle 4 stroke:red,stroke-width:2px,color:red;
