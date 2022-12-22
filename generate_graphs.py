import numpy as np
import pickle
import matplotlib.pyplot as plt

def clean(filename, out_filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    data = {"Cartierwristwatch":{}, "PalmPilotM515PDA":{}, "Xboxgameconsole":{}} #seperated by category, then auction
    previousAuctionId = None
    previousBidder = None
    previousHighestBid = None
    for line in lines[1:]:
        line = line.replace(" ", "").replace('"', "") #remove spaces and quotes from line
        line = line.split(",") #turn line into array of column data
        del line[4] #remove bidderrate column
        line[7] = int(line[7][0]) #turn "3 day auction" into int(3)
        for i in [1, 2, 4, 5]: #turn string values to floats
            line[i] = float(line[i])
        line[2] = line[2]/line[7] #normalize bid time from 0 to 1
        line[0] = int(line[0])
        auction_id = line[0]
        bid = line[1]
        bidder = line[3]
        opening_bid = line[4]
        category = line[6]
        if bid < opening_bid: continue #ignore bids that don't meet the minimum bid
        if previousAuctionId != None and auction_id == previousAuctionId:
            if previousHighestBid != None and bid <= previousHighestBid: continue #ignore bids that don't beat the previous highest bid 
            if previousBidder != None and bidder == previousBidder: #combine new bids by the same bidder into one bid with highest price
                previousHighestBid = bid
                data[category][auction_id]["bids"][-1] = line[1:4] #overwrite previous bid with this one
                continue
        else:
            data[category][auction_id] = {"bids":[], "duration":line[7], "open":opening_bid}
        #if we change to new auction and/or include this bid, set previous values
        previousAuctionId = auction_id
        previousBidder = bidder
        previousHighestBid = bid
        data[category][auction_id]["bids"].append(line[1:4])
    with open(out_filename, 'wb') as handle:
        pickle.dump(data, handle)
    return data

def makeBidDistributionGraphs(data, category = None):
    #makes four graphs: 2d graph for bid winners that graphs the distribution over time of bids and how many winners bid at that time
                    #   then the same one for bid losers
                    #   2d graph for bid winners that graphs bid increment over time, and how many winners bid at that time
                    #   then the same for bid losers
                    #   2d graph for when the winning bid is placed over time
                    #   2d graph for the winning bid increment over time
    bidWinners = []
    bidLosers = []

    for item, auctions in data.items():
        if category != None and item != category: continue 
        for auction_id, auction_info in auctions.items():
            bidWinners.append(auction_info["bids"][-1][2]) #last bidder is always the winner
            for bid in auction_info["bids"]:
                if bid[2] not in bidWinners and bid[2] not in bidLosers: bidLosers.append(bid[2]) #add all other bidders as losers

    winning_bidder_graph_data = ([], []) 
    losing_bidder_graph_data = ([], [])  

    for category, auctions in data.items():
        for auction_id, auction_info in auctions.items():
            previousBid = auction_info["open"]
            final_bid = auction_info["bids"][-1][0]
            for bid in auction_info["bids"]:
                bid_increment = (bid[0] - previousBid)/final_bid
                previousBid = bid[0]
                if bid[2] in bidWinners:
                    winning_bidder_graph_data[0].append(bid[1])
                    winning_bidder_graph_data[1].append(bid_increment)
                else:
                    losing_bidder_graph_data[0].append(bid[1])
                    losing_bidder_graph_data[1].append(bid_increment)

    return winning_bidder_graph_data, losing_bidder_graph_data

def generateGraphs(graph1, graph2, extraKeyword="", crop=None, show=True):
    #graph1 is for winners, graph2 is for losers
    #graph3 is for the winning bids, graph4 is for the last losing bid
    if crop == None:
        plt.hist(graph1[0], bins=50)
        plt.xlabel("Winning bidders' bid time (normalized)")
        plt.ylabel("Number of bids")
        plt.savefig('plots/winner_bids_time_distrib' + extraKeyword + '.png')
        if show: plt.show()
        else: plt.clf()

        plt.hist(graph2[0], bins=50)
        plt.xlabel("Losing bidders' bid time (normalized)")
        plt.ylabel("Number of bids")
        plt.savefig('plots/loser_bids_time_distrib' + extraKeyword + '.png')
        if show: plt.show()
        else: plt.clf()

    scatter_point_alpha = 0.5
    scatter_point_size = 3

    sorted_graph1 = ([], [])
    #sort values based on bid time, so we can generate running average
    for bid_time, bid_increment in sorted(zip(graph1[0], graph1[1])):
        sorted_graph1[0].append(bid_time)
        sorted_graph1[1].append(bid_increment)

    num_bins = 50
    window = round(len(sorted_graph1[0])/num_bins) #window is number of values we include in our average at each step
    #compute running average of bid increments with window size
    running_average = []
    for i in range(len(sorted_graph1[1]) - window + 1):
        running_average.append(np.mean(sorted_graph1[1][i:i+window]))

    plt.scatter(sorted_graph1[0], sorted_graph1[1], s=scatter_point_size, alpha=scatter_point_alpha)
    plt.plot(sorted_graph1[0][:len(running_average)], running_average ,"r")
    plt.xlabel("Winning bidders' bid time (normalized)")
    plt.ylabel("Bid increment (normalized)\nRunning average in red")
    if crop != None: plt.axis(crop)
    plt.savefig('plots/winners_bid_increment_time_distrib' + extraKeyword + '.png')
    if show: plt.show()
    else: plt.clf()

    sorted_graph2 = ([], [])
    #sort values based on bid time, so we can generate running average
    for bid_time, bid_increment in sorted(zip(graph2[0], graph2[1])):
        sorted_graph2[0].append(bid_time)
        sorted_graph2[1].append(bid_increment)
    
    window = int(len(sorted_graph2[0])/num_bins)
    running_average = []
    for i in range(len(sorted_graph2[1]) - window + 1):
        running_average.append(np.mean(sorted_graph2[1][i:i+window]))

    plt.scatter(sorted_graph2[0], sorted_graph2[1], s=scatter_point_size, alpha=scatter_point_alpha)
    plt.plot(sorted_graph2[0][:len(running_average)], running_average ,"r")
    plt.xlabel("Losing bidders' bid time (normalized)")
    plt.ylabel("Bid increment (normalized)\nRunning average in red")
    if crop != None: plt.axis(crop)
    plt.savefig('plots/losers_bid_increment_time_distrib' + extraKeyword + '.png')
    if show: plt.show()
    else: plt.clf()


if __name__ == "__main__":
    clean_data_filename = "data/cleaned_data.sav"
    try:
        with open(clean_data_filename, 'rb') as handle:
            clean_data = pickle.load(handle)
    except FileNotFoundError:
        raw_data_filename = "data/auction.csv"
        print("No pre-cleaned data detected. Cleaning " + raw_data_filename)
        clean_data = clean(raw_data_filename, clean_data_filename)

    graph1, graph2 = makeBidDistributionGraphs(clean_data)

    generateGraphs(graph1, graph2, show=False)
    generateGraphs(graph1, graph2, crop=[0.8, 1.0, 0.0, 0.2], extraKeyword="_cropped", show=False)
    
    #removed, since seperate plots for each item category did not offer any additional insights

    #for item_category in ["Cartierwristwatch", "PalmPilotM515PDA", "Xboxgameconsole"]:
    #    graph1, graph2 = makeBidDistributionGraphs(clean_data, item_category)
    #    generateGraphs(graph1, graph2, crop=[0.9, 1.0, 0.0, 0.4], extraKeyword="_cropped_"+item_category)