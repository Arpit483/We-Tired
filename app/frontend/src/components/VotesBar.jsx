import React from 'react';

const VotesBar = ({ votes, total = 32, colorClass }) => {
  const segments = [];
  for (let i = 0; i < total; i++) {
    if (i < votes) {
      segments.push(<div key={i} className={`flex-1 ${colorClass}`}></div>);
    } else {
      segments.push(<div key={i} className="flex-1"></div>);
    }
  }

  const borderClass = colorClass.replace('-bg', '-border');

  return (
    <div className={`w-full h-4 border flex p-[1px] gap-[1px] ${borderClass}`}>
      {segments}
    </div>
  );
};

export default React.memo(VotesBar, (prevProps, nextProps) => prevProps.votes === nextProps.votes && prevProps.colorClass === nextProps.colorClass);
