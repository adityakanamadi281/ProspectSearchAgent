from collections import defaultdict
from typing import List
from .api_clients.apollo import ApolloClient
from .api_clients.crunchbase import CrunchbaseClient # Mocked
from .api_clients.serpapi import SerpApiClient # Mocked
from .utils import Prospect, calculate_confidence_score

class ProspectSearchAgent:
    def __init__(self, icp: dict):
        self.icp = icp
        self.apollo_client = ApolloClient()
        # self.crunchbase_client = CrunchbaseClient() # Init real clients
        # self.serpapi_client = SerpAPIClient() 

    async def _fetch_all_data(self) -> List[Prospect]:
        """
        Asynchronously fetches data from all sources.
        In a real application, this would use `asyncio.gather`.
        """
        print("-> Fetching data from Apollo...")
        apollo_prospects = self.apollo_client.search_companies(self.icp)
        print(f"-> Found {len(apollo_prospects)} prospects from Apollo.")

        # Vibe-coded: Mock results from other sources
        crunchbase_signals = [{'domain': p.domain, 'new_funding': (i % 3 == 0)} for i, p in enumerate(apollo_prospects)]
        serpapi_signals = [{'domain': p.domain, 'recent_hiring': (i % 2 == 0), 'tech_stack_match': (i % 5 == 0)} for i, p in enumerate(apollo_prospects)]
        
        # Real logic:
        # apollo_prospects = await self.apollo_client.search_companies(self.icp)
        # crunchbase_data = await self.crunchbase_client.get_funding_signals(apollo_prospects)
        # serpapi_data = await self.serpapi_client.get_hiring_signals(apollo_prospects)
        
        return apollo_prospects, crunchbase_signals, serpapi_signals

    def _merge_and_deduplicate(self, all_data) -> List[Prospect]:
        """Combines and deduplicates results using company domain as key."""
        
        apollo_prospects, cb_signals, serp_signals = all_data
        
        # 1. Initial Load and Deduplication (by domain)
        prospects_by_domain = {p.domain: p for p in apollo_prospects} # Apollo is primary
        
        # 2. Enrich with Signals
        all_signals = cb_signals + serp_signals
        
        for signal in all_signals:
            domain = signal.get('domain')
            if domain in prospects_by_domain:
                prospect = prospects_by_domain[domain]
                # Merge signals
                prospect.signals.update(signal)
                # Track source
                if 'new_funding' in signal:
                    prospect.source.add('Crunchbase')
                if 'recent_hiring' in signal:
                    prospect.source.add('SerpAPI')

        # 3. Contact Deduplication (by email within each prospect)
        for prospect in prospects_by_domain.values():
            unique_contacts = {}
            for contact in prospect.contacts:
                if contact.email not in unique_contacts:
                    unique_contacts[contact.email] = contact
            prospect.contacts = list(unique_contacts.values())

        return list(prospects_by_domain.values())

    def run(self) -> List[dict]:
        """Orchestrates the entire prospect search and processing."""
        
        # Step 1: Fetch data (Mocking the async call for simplicity here)
        all_data = self._fetch_all_data()

        # Step 2: Merge and Deduplicate
        final_prospects = self._merge_and_deduplicate(all_data)

        # Step 3: Score and Finalize
        print("-> Calculating confidence scores...")
        for prospect in final_prospects:
            calculate_confidence_score(prospect, self.icp)

        # Sort by confidence score
        final_prospects.sort(key=lambda p: p.confidence, reverse=True)

        return [p.to_dict() for p in final_prospects]
    