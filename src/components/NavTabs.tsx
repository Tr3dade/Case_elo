import React from 'react';

interface NavTabsProps {
  tabs: string[];
  currentTab: number;
  onTabChange: (index: number) => void;
}

const NavTabs: React.FC<NavTabsProps> = ({ tabs, currentTab, onTabChange }) => {
  return (
    <div className="nav-tabs">
      {tabs.map((tab, tabIndex) => (
        <div
          key={tabIndex}
          className={`nav-tab ${tabIndex === currentTab ? 'active' : ''}`}
          onClick={() => onTabChange(tabIndex)}
        >
          {tab}
        </div>
      ))}
    </div>
  );
};

export default NavTabs;